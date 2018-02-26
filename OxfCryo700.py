import PyTango
import sys
import threading

import serial

from oxfordcryo import StatusPacket, CSCOMMAND, splitBytes


class OxfCryo700Class(PyTango.DeviceClass):
    cmd_list = {
        'Restart': [[PyTango.ArgType.DevVoid, ""],
                    [PyTango.ArgType.DevVoid, ""]],

        'Stop': [[PyTango.ArgType.DevVoid, ""],
                 [PyTango.ArgType.DevVoid, ""]],

        'Purge': [[PyTango.ArgType.DevVoid, ""],
                  [PyTango.ArgType.DevVoid, ""]],

        'Turbo': [[PyTango.ArgType.DevVarStringArray,
                   "Turbo (0 or 1 Switch Turbo)"],
                  [PyTango.ArgType.DevVoid, ""]],

        'Cool': [[PyTango.ArgType.DevDouble,
                  "Temperature in Kelvins,Value between 80 to 400 "],
                 [PyTango.ArgType.DevVoid, ""]],

        'Ramp': [[PyTango.ArgType.DevVarStringArray,
                  "Rate, FinalTemperature"],
                 [PyTango.ArgType.DevVoid, ""]],

        'Pause': [[PyTango.ArgType.DevVoid,
                   "Pause command identifier - enter temporary Hold"],
                  [PyTango.ArgType.DevVoid, ""]],

        'Plat': [[PyTango.ArgType.DevDouble,
                  "Plat command identifier - parameter follows"],
                 [PyTango.ArgType.DevVoid, ""]],

        'End': [[PyTango.ArgType.DevDouble,
                 "End command identifier - parameter follows"],
                [PyTango.ArgType.DevVoid, ""]],

        'Resume': [[PyTango.ArgType.DevVoid,
                    "Resume cmd identifier - exit temporary Hold"],
                   [PyTango.ArgType.DevVoid, ""]],

        'CryoShutter_Start_Auto': [[PyTango.ArgType.DevDouble,
                                    "Shut the CryoShutter for the "
                                    "specified length of time"],
                                   [PyTango.ArgType.DevVoid, ""]],

        'CryoShutter_Start_Man': [[PyTango.ArgType.DevVoid,
                                   "Shut the CryoShutter until a "
                                   "CSCOMMAND_CRYOSHUTTER_STOP is "
                                   "received"],
                                  [PyTango.ArgType.DevVoid, ""]],

        'CryoShutter_Stop': [[PyTango.ArgType.DevVoid,
                              "Open the CryoShutter"],
                             [PyTango.ArgType.DevVoid, ""]],

        'Status_Format': [[PyTango.ArgType.DevVarStringArray,
                           "Set status packet format"],
                          [PyTango.ArgType.DevVoid, ""]],

    }

    attr_list = {
        'GasSetPoint': [[PyTango.ArgType.DevDouble,
                         PyTango.AttrDataFormat.SCALAR,
                         PyTango.AttrWriteType.READ],
                        {'unit': 'K'}],
        'GasTemp': [[PyTango.ArgType.DevDouble,
                     PyTango.AttrDataFormat.SCALAR,
                     PyTango.AttrWriteType.READ],
                    {'unit': 'K'}],
        'GasError': [[PyTango.ArgType.DevDouble,
                      PyTango.AttrDataFormat.SCALAR,
                      PyTango.AttrWriteType.READ],
                     {'unit': 'K'}],
        'RunMode': [[PyTango.ArgType.DevString,
                     PyTango.AttrDataFormat.SCALAR,
                     PyTango.AttrWriteType.READ]],
        'Phase': [[PyTango.ArgType.DevString,
                   PyTango.AttrDataFormat.SCALAR,
                   PyTango.AttrWriteType.READ]],
        'RampRate': [[PyTango.ArgType.DevLong,
                      PyTango.AttrDataFormat.SCALAR,
                      PyTango.AttrWriteType.READ],
                     {'unit': 'K/h'}],
        'TargetTemp': [[PyTango.ArgType.DevDouble,
                        PyTango.AttrDataFormat.SCALAR,
                        PyTango.AttrWriteType.READ]],
        'EvapTemp': [[PyTango.ArgType.DevDouble,
                      PyTango.AttrDataFormat.SCALAR,
                      PyTango.AttrWriteType.READ],
                     {'unit': 'K'}],
        'SuctTemp': [[PyTango.ArgType.DevDouble,
                      PyTango.AttrDataFormat.SCALAR,
                      PyTango.AttrWriteType.READ],
                     {'unit': 'K'}],
        'GasFlow': [[PyTango.ArgType.DevDouble,
                     PyTango.AttrDataFormat.SCALAR,
                     PyTango.AttrWriteType.READ],
                    {'unit': 'l/min'}],
        'GasHeat': [[PyTango.ArgType.DevLong,
                     PyTango.AttrDataFormat.SCALAR,
                     PyTango.AttrWriteType.READ],
                    {'unit': '%'}],
        'EvapHeat': [[PyTango.ArgType.DevLong,
                      PyTango.AttrDataFormat.SCALAR,
                      PyTango.AttrWriteType.READ],
                     {'unit': '%'}],
        'SuctHeat': [[PyTango.ArgType.DevLong,
                      PyTango.AttrDataFormat.SCALAR,
                      PyTango.AttrWriteType.READ],
                     {'unit': '%'}],
        'LinePressure': [[PyTango.ArgType.DevDouble,
                          PyTango.AttrDataFormat.SCALAR,
                          PyTango.AttrWriteType.READ],
                         {'unit': 'bar'}],
        'Alarm': [[PyTango.ArgType.DevString,
                   PyTango.AttrDataFormat.SCALAR,
                   PyTango.AttrWriteType.READ]],
        'RunTime': [[PyTango.ArgType.DevString,
                     PyTango.AttrDataFormat.SCALAR,
                     PyTango.AttrWriteType.READ]],
        'ControllerNr': [[PyTango.ArgType.DevLong,
                          PyTango.AttrDataFormat.SCALAR,
                          PyTango.AttrWriteType.READ]],
        'SoftwareVersion': [[PyTango.ArgType.DevLong,
                             PyTango.AttrDataFormat.SCALAR,
                             PyTango.AttrWriteType.READ]],
        'EvapAdjust': [[PyTango.ArgType.DevLong,
                        PyTango.AttrDataFormat.SCALAR,
                        PyTango.AttrWriteType.READ]],
        'TurboMode': [[PyTango.ArgType.DevBoolean,
                       PyTango.AttrDataFormat.SCALAR,
                       PyTango.AttrWriteType.READ]],

    }

    device_property_list = {
        'serialPort': [PyTango.DevString,
                       "name of the serial port (/dev/ttyXX)",
                       []]
    }

    def __init__(self, name):
        PyTango.DeviceClass.__init__(self, name)
        self.set_type("TestDevice")


class OxfCryo700(PyTango.Device_4Impl):
    def __init__(self, cl, name):
        PyTango.Device_4Impl.__init__(self, cl, name)
        self.info_stream('In OxfCryo700.__init__')
        OxfCryo700.init_device(self)

    @PyTango.DebugIt()
    def init_device(self):
        self.info_stream('In Python init_device method')
        self.get_device_properties(self.get_device_class())
        self.serial = serial.Serial(self.serialPort)
        self.statusPacket = None
        self.statusThread = threading.Thread(group=None,
                                             target=self.updateStatusPacket)
        self.statusThreadStop = threading.Event()
        self.statusThread.start()
        self.set_state(PyTango.DevState.ON)
        self.attr_short_rw = 66
        self.attr_long = 1246

    # ------------------------------------------------------------------

    @PyTango.DebugIt()
    def delete_device(self):
        self.statusThreadStop.set()
        self.statusThread.join(3.0)
        self.info_stream('OxfCryo700.delete_device')

    # ------------------------------------------------------------------
    # COMMANDS
    # ------------------------------------------------------------------

    def is_Restart_allowed(self):
        return self.get_state() == PyTango.DevState.ON

    @PyTango.DebugIt()
    def Restart(self):
        data = [chr(2), chr(CSCOMMAND.RESTART)]
        dataStr = ''.join(data)
        self.debug_stream("Restart(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def Purge(self):
        data = [chr(2), chr(CSCOMMAND.PURGE)]
        dataStr = ''.join(data)
        self.debug_stream("PURGE(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    def is_Stop_allowed(self):
        return self.get_state() == PyTango.DevState.ON

    @PyTango.DebugIt()
    def Stop(self):
        data = [chr(2), chr(CSCOMMAND.STOP)]
        dataStr = ''.join(data)
        self.debug_stream("Stop(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    def is_Ramp_allowed(self):
        return self.get_state() == PyTango.DevState.ON

    @PyTango.DebugIt()
    def Ramp(self, args):
        """
        The CSCOMMAND_RAMP command packet, size = 6
        The Params[] array consists of a short containing desired ramp rate
        in K/hour,
        followed by a short containing the end temperature in centi-Kelvin
        """

        if len(args) != 2:
            raise Exception(
                "Wrong number of arguments. Required paramters are ramp and "
                "end temperature.")
        try:
            rate = int(args[0])
            finalTemp = float(args[1])
        except:
            raise Exception(
                "Wrong type of arguments. Ramp must be an integer and end "
                "temperature a float number.")
        finalTemp = int(finalTemp * 100)  # transfering to centi-Kelvin
        rateHigh, rateLow = splitBytes(rate)
        finalTempHigh, finalTempLow = splitBytes(finalTemp)
        data = [chr(6), chr(CSCOMMAND.RAMP), rateHigh, rateLow, finalTempHigh,
                finalTempLow]
        dataStr = ''.join(data)
        self.debug_stream("Ramp(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def Turbo(self, args):
        """
        The CSCOMMAND_TURBO command packet, size = 3
        The Params[] array consists of a single char taking the value either 0
        (switch Turbo off) or 1 (switch Turbo on)
        """
        if len(args) != 1:
            raise Exception(
                "Wrong number of arguments. Required paramters 0 (switch "
                "Turbo off) or 1 (switch Turbo on).")
        try:
            turboState = int(args[0])

            if turboState != 0 and turboState != 1:
                raise Exception()

        except:
            raise Exception(
                "Wrong type of arguments. Turbo must be an integer, "
                "0 (switch Turbo off) or 1 (switch Turbo on). .")

        data = [chr(3), chr(CSCOMMAND.TURBO), turboState]
        dataStr = ''.join(data)
        self.debug_stream("Turbo(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def Cool(self, temp):
        """
        The	CSCOMMAND_COOL command packet, size = 4
        The Params[] array consists of a short containing the end
        temperature in centi-Kelvin
        """
        try:
            coolValue = temp
            if not (80 <= coolValue <= 400):
                raise Exception()
        except:
            raise Exception(
                "Wrong arguments. Cool only accept values between 80 to 400")

        coolValue = int(coolValue * 100)
        HIBYTE, LOBYTE = splitBytes(coolValue)

        data = [chr(4), chr(CSCOMMAND.COOL), HIBYTE, LOBYTE]
        dataStr = ''.join(data)
        self.debug_stream("Cool(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def Pause(self):
        data = [chr(2), chr(CSCOMMAND.PAUSE)]
        dataStr = ''.join(data)
        self.debug_stream("Pause(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def Resume(self):
        data = [chr(2), chr(CSCOMMAND.RESUME)]
        dataStr = ''.join(data)
        self.debug_stream("Resume(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def Plat(self, time):
        """
        The CSCOMMAND_PLAT command packet, size = 4
        The Params[] array consists of a short containing the duration of the
        Plat in minutes
        """

        val = int(time)
        HIBYTE, LOBYTE = splitBytes(val)
        data = [chr(4), chr(CSCOMMAND.PLAT), HIBYTE, LOBYTE]
        dataStr = ''.join(data)
        self.debug_stream("Plat(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def End(self, values):
        """
        The CSCOMMAND_END command packet, size = 4
        The Params[] array consists of a short containing desired ramp rate
        in K/hour
        """

        val = int(values)
        HIBYTE, LOBYTE = splitBytes(val)
        data = [chr(4), chr(CSCOMMAND.END), HIBYTE, LOBYTE]
        dataStr = ''.join(data)
        self.debug_stream("End(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def CryoShutter_Start_Auto(self, values):
        """
        The CSCOMMAND_CRYOSHUTTER_START_AUTO command packet, size = 3
        The Params[] array consists of a short containing the duration of the
        anneal time in tenths of a second
        """
        val = int(values * 10)
        data = [chr(3), chr(CSCOMMAND.CRYOSHUTTER_START_AUTO), str(val)]
        dataStr = ''.join(data)
        self.debug_stream(
            "CryoShutter_Start_Auto(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def CryoShutter_Start_Man(self):
        """
        The	CSCOMMAND_CRYOSHUTTER_START_MAN command packet, size = 2
        Shut until CSCOMMAND_CRYOSHUTTER_STOP
        """
        data = [chr(2), chr(CSCOMMAND.CRYOSHUTTER_START_MAN)]
        dataStr = ''.join(data)
        self.debug_stream(
            "CryoShutter_Start_Man(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def CryoShutter_Stop(self):
        """
        The	CSCOMMAND_CRYOSHUTTER_STOP command packet, size = 2
        Open the CryoShutter
        """
        data = [chr(2), chr(CSCOMMAND.CRYOSHUTTER_STOP)]
        dataStr = ''.join(data)
        self.debug_stream("CryoShutter_Stop(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    def Status_Format(self, args):
        """
        The CSCOMMAND_SETSTATUSFORMAT command packet, size = 3
        """

        if len(args) != 1:
            raise Exception(
                "Wrong number of arguments. Required paramters 0 or 1.")
        try:
            val = int(args[0])
            if val != 0 and val != 1:
                raise Exception()
        except:
            raise Exception(
                "Wrong type of arguments. Status_Format must be an integer, "
                "0 or 1.")

        data = [chr(3), chr(CSCOMMAND.SETSTATUSFORMAT), val]
        dataStr = ''.join(data)
        self.debug_stream("Status_Format(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    # ------------------------------------------------------------------
    # ATTRIBUTES
    # ------------------------------------------------------------------

    @PyTango.DebugIt()
    def read_attr_hardware(self, data):
        self.info_stream('In read_attr_hardware')

    @PyTango.DebugIt()
    def is_GasSetPoint_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_GasSetPoint(self, the_att):
        self.info_stream("read_GasSetPoint")
        gasSetPoint = self.statusPacket.gas_set_point
        the_att.set_value(gasSetPoint)

    @PyTango.DebugIt()
    def is_GasTemp_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_GasTemp(self, the_att):
        self.info_stream("read_GasSetPoint")
        gasTemp = self.statusPacket.gas_temp
        the_att.set_value(gasTemp)

    @PyTango.DebugIt()
    def is_GasError_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_GasError(self, the_att):
        self.info_stream("read_GasError")
        gasError = self.statusPacket.gas_error
        the_att.set_value(gasError)

    @PyTango.DebugIt()
    def is_RunMode_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_RunMode(self, the_att):
        self.info_stream("read_RunMode")
        runMode = self.statusPacket.run_mode
        the_att.set_value(runMode)

    @PyTango.DebugIt()
    def is_Phase_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_Phase(self, the_att):
        self.info_stream("read_Phase")
        phase = self.statusPacket.phase
        the_att.set_value(phase)

    @PyTango.DebugIt()
    def is_RampRate_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_RampRate(self, the_att):
        self.info_stream("read_RampRate")
        rampRate = self.statusPacket.ramp_rate
        the_att.set_value(rampRate)

    @PyTango.DebugIt()
    def is_TargetTemp_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_TargetTemp(self, the_att):
        self.info_stream("read_TargetTemp")
        targetTemp = self.statusPacket.target_temp
        the_att.set_value(targetTemp)

    @PyTango.DebugIt()
    def is_EvapTemp_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_EvapTemp(self, the_att):
        self.info_stream("read_EvapTemp")
        evapTemp = self.statusPacket.evap_temp
        the_att.set_value(evapTemp)

    @PyTango.DebugIt()
    def is_SuctTemp_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_SuctTemp(self, the_att):
        self.info_stream("read_SuctTemp")
        suctTemp = self.statusPacket.suct_temp
        the_att.set_value(suctTemp)

    @PyTango.DebugIt()
    def is_GasFlow_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_GasFlow(self, the_att):
        self.info_stream("read_GasFlow")
        gasFlow = self.statusPacket.gas_flow
        the_att.set_value(gasFlow)

    @PyTango.DebugIt()
    def is_GasHeat_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_GasHeat(self, the_att):
        self.info_stream("read_GasHeat")
        gasHeat = self.statusPacket.gas_heat
        the_att.set_value(gasHeat)

    @PyTango.DebugIt()
    def is_EvapHeat_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_EvapHeat(self, the_att):
        self.info_stream("read_EvapHeat")
        evapHeat = self.statusPacket.evap_heat
        the_att.set_value(evapHeat)

    @PyTango.DebugIt()
    def is_SuctHeat_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_SuctHeat(self, the_att):
        self.info_stream("read_SuctHeat")
        suctHeat = self.statusPacket.suct_heat
        the_att.set_value(suctHeat)

    @PyTango.DebugIt()
    def is_LinePressure_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_LinePressure(self, the_att):
        self.info_stream("read_LinePressure")
        linePressure = self.statusPacket.line_pressure
        the_att.set_value(linePressure)

    @PyTango.DebugIt()
    def is_Alarm_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_Alarm(self, the_att):
        self.info_stream("read_Alarm")
        alarm = self.statusPacket.alarm
        the_att.set_value(alarm)

    @PyTango.DebugIt()
    def is_RunTime_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_RunTime(self, the_att):
        self.info_stream("read_RunTime")
        runTime = "%dd, %dh, %dm" % (self.statusPacket.run_days,
                                     self.statusPacket.run_hours,
                                     self.statusPacket.run_mins)
        the_att.set_value(runTime)

    @PyTango.DebugIt()
    def is_ControllerNumber_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_ControllerNr(self, the_att):
        self.info_stream("read_ControllerNumber")
        nr = self.statusPacket.controller_nb
        the_att.set_value(nr)

    @PyTango.DebugIt()
    def is_ControllerNr_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_SoftwareVersion(self, the_att):
        self.info_stream("read_SoftwareVersion")
        ver = self.statusPacket.software_version
        the_att.set_value(ver)

    @PyTango.DebugIt()
    def is_EvepAdjust_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_EvapAdjust(self, the_att):
        self.info_stream("read_EvapAdjust")
        evapAdjust = self.statusPacket.evap_adjust
        the_att.set_value(evapAdjust)

    @PyTango.DebugIt()
    def is_TurboMode_allowed(self, req_type):
        return self.get_state() in (PyTango.DevState.ON,)

    @PyTango.DebugIt()
    def read_TurboMode(self, the_att):
        self.info_stream("read_TurboModet")
        flow = self.statusPacket.gas_flow
        phase = self.statusPacket.phase
        self.info_stream("flow: %f , phase: %s " % (flow, phase))
        if flow > 5 and phase != "Cool":
            turbomode = True
        else:
            turbomode = False
        the_att.set_value(turbomode)

    @PyTango.InfoIt()
    def updateStatusPacket(self):
        self.statusThreadStop.clear()
        # flushing input buffer
        self.flushInputBuffer()
        # updaitng loop
        while not self.statusThreadStop.isSet():
            data = self.serial.read(32)
            # if there are newer packets in the buffer, we do not process
            # and just continue
            if self.serial.inWaiting() > 32:
                continue
            else:
                data = map(ord, data)
                try:
                    self.statusPacket = StatusPacket(data)
                except Exception, e:
                    self.error_stream("Error while parsing read data: %s" % e)
                    self.error_stream(
                        "Flushing input buffer to start from the skratch")
                    self.flushInputBuffer()

    def flushInputBuffer(self):
        while self.serial.inWaiting() > 0:
            self.serial.flushInput()


if __name__ == '__main__':
    util = PyTango.Util(sys.argv)
    util.add_class(OxfCryo700Class, OxfCryo700)

    U = PyTango.Util.instance()
    U.server_init()
    U.server_run()
