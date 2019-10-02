import sys
import threading
import serial
import PyTango
from tango import DevState
from tango.server import Device, attribute, command
from tango.server import device_property
from oxfordcryo import StatusPacket, CSCOMMAND, splitBytes


class OxfCryo700(Device):
    port = device_property(dtype=str, doc='Serial port name (/dev/ttyXX)')

    def init_device(self):
        Device.init_device(self)
        self.info_stream('In Python init_device method')
        self.serial = serial.Serial(self.port)
        self.statusPacket = None
        self.statusThread = threading.Thread(group=None,
                                             target=self.updateStatusPacket)
        self.statusThreadStop = threading.Event()
        self.statusThread.start()
        self.set_state(DevState.ON)
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

    @PyTango.DebugIt()
    @command
    def Restart(self):
        data = [chr(2), chr(CSCOMMAND.RESTART)]
        dataStr = ''.join(data)
        self.debug_stream("Restart(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command
    def Purge(self):
        data = [chr(2), chr(CSCOMMAND.PURGE)]
        dataStr = ''.join(data)
        self.debug_stream("PURGE(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command
    def Stop(self):
        data = [chr(2), chr(CSCOMMAND.STOP)]
        dataStr = ''.join(data)
        self.debug_stream("Stop(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command(dtype_in=(float,), doc_in='Rate and FinalTemperature')
    def Ramp(self, args):
        """
        The CSCOMMAND_RAMP command packet, size = 6
        The Params[] array consists of a short containing desired ramp rate
        in K/hour,
        followed by a short containing the end temperature in centi-Kelvin
        """

        if len(args) != 2:
            raise ValueError("Wrong number of arguments. Required paramters "
                             "are ramp and end temperature.")

        rate = int(args[0])
        finalTemp = args[1]

        finalTemp = int(finalTemp * 100)  # transfering to centi-Kelvin
        rateHigh, rateLow = splitBytes(rate)
        finalTempHigh, finalTempLow = splitBytes(finalTemp)
        data = [chr(6), chr(CSCOMMAND.RAMP), rateHigh, rateLow, finalTempHigh,
                finalTempLow]
        dataStr = ''.join(data)
        self.debug_stream("Ramp(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command(dtype_in=bool, doc_in='Turn on the Turbo')
    def Turbo(self, turn_on):
        """
        The CSCOMMAND_TURBO command packet, size = 3
        The Params[] array consists of a single char taking the value either 0
        (switch Turbo off) or 1 (switch Turbo on)
        """
        if turn_on:
            turboState = 1
        else:
            turboState = 0
        data = [chr(3), chr(CSCOMMAND.TURBO), turboState]
        dataStr = ''.join(data)
        self.debug_stream("Turbo(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command(dtype_in=float, doc_in='Temperature between 80 to 400 Kelvins')
    def Cool(self, temp):
        """
        The	CSCOMMAND_COOL command packet, size = 4
        The Params[] array consists of a short containing the end
        temperature in centi-Kelvin
        """
        if not (80 <= temp <= 400):
            raise ValueError("Wrong arguments. Cool only accept values "
                             "between 80 to 400")

        cool_value = int(temp * 100)
        HIBYTE, LOBYTE = splitBytes(cool_value)

        data = [chr(4), chr(CSCOMMAND.COOL), HIBYTE, LOBYTE]
        dataStr = ''.join(data)
        self.debug_stream("Cool(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command
    def Pause(self):
        data = [chr(2), chr(CSCOMMAND.PAUSE)]
        dataStr = ''.join(data)
        self.debug_stream("Pause(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command
    def Resume(self):
        data = [chr(2), chr(CSCOMMAND.RESUME)]
        dataStr = ''.join(data)
        self.debug_stream("Resume(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command(dtype_in=int, doc_in='Plat command identifier - parameter '
                                  'follows')
    def Plat(self, val):
        """
        The CSCOMMAND_PLAT command packet, size = 4
        The Params[] array consists of a short containing the duration of the
        Plat in minutes
        """

        HIBYTE, LOBYTE = splitBytes(val)
        data = [chr(4), chr(CSCOMMAND.PLAT), HIBYTE, LOBYTE]
        dataStr = ''.join(data)
        self.debug_stream("Plat(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command(dtype_in=int, doc_in='End command identifier - parameter follows')
    def End(self, val):
        """
        The CSCOMMAND_END command packet, size = 4
        The Params[] array consists of a short containing desired ramp rate
        in K/hour
        """

        HIBYTE, LOBYTE = splitBytes(val)
        data = [chr(4), chr(CSCOMMAND.END), HIBYTE, LOBYTE]
        dataStr = ''.join(data)
        self.debug_stream("End(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command(dtype_in=float, doc_in='Shyt the Cryosutter for the specified '
                                    'length of time.')
    def CryoShutter_Start_Auto(self, value):
        """
        The CSCOMMAND_CRYOSHUTTER_START_AUTO command packet, size = 3
        The Params[] array consists of a short containing the duration of the
        anneal time in tenths of a second
        """
        val = int(value * 10)
        data = [chr(3), chr(CSCOMMAND.CRYOSHUTTER_START_AUTO), str(val)]
        dataStr = ''.join(data)
        self.debug_stream(
            "CryoShutter_Start_Auto(): sending data: %s" % dataStr)
        self.serial.write(dataStr)

    @PyTango.DebugIt()
    @command
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
    @command
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
    @command(dtype_in=(str,), doc_in='Set status packet format')
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
    @attribute(name='GasSetPoint', unit='K')
    def gas_set_point(self):
        self.info_stream("read_GasSetPoint")
        return self.statusPacket.gas_set_point

    @PyTango.DebugIt()
    @attribute(name='GasTemp', unit='K')
    def gas_temp(self):
        self.info_stream("read_GasSetPoint")
        return self.statusPacket.gas_temp

    @PyTango.DebugIt()
    @attribute(name='GasError', unit='K')
    def gas_error(self):
        self.info_stream("read_GasError")
        return self.statusPacket.gas_error

    @PyTango.DebugIt()
    @attribute(name='RunMode', dtype=str)
    def run_mode(self):
        self.info_stream("read_RunMode")
        return self.statusPacket.run_mode

    @PyTango.DebugIt()
    @attribute(name='Phase', dtype=str)
    def read_Phase(self):
        self.info_stream("read_Phase")
        return self.statusPacket.phase

    @PyTango.DebugIt()
    @attribute(name='RampRate', dtype=int)
    def ramp_rate(self):
        self.info_stream("read_RampRate")
        return self.statusPacket.ramp_rate

    @PyTango.DebugIt()
    @attribute(name='TargetTemp')
    def target_temp(self, the_att):
        self.info_stream("read_TargetTemp")
        return self.statusPacket.target_temp

    @PyTango.DebugIt()
    @attribute(name='EvapTemp', unit='K')
    def read_EvapTemp(self):
        self.info_stream("read_EvapTemp")
        return self.statusPacket.evap_temp

    @PyTango.DebugIt()
    @attribute(name='SuctTemp', unit='K')
    def suct_temp(self):
        self.info_stream("read_SuctTemp")
        return self.statusPacket.suct_temp

    @PyTango.DebugIt()
    @attribute(name='GasFlow', unit='l/min')
    def gas_flow(self):
        self.info_stream("read_GasFlow")
        return self.statusPacket.gas_flow

    @PyTango.DebugIt()
    @attribute(name='GasHeat', unit='%')
    def gas_heat(self):
        self.info_stream("read_GasHeat")
        return self.statusPacket.gas_heat

    @PyTango.DebugIt()
    @attribute(name='EvapHeat', unit='%')
    def evap_heat(self):
        self.info_stream("read_EvapHeat")
        return self.statusPacket.evap_heat

    @PyTango.DebugIt()
    @attribute(name='SuctHeat', unit='%')
    def suct_heat(self):
        self.info_stream("read_SuctHeat")
        return self.statusPacket.suct_heat

    @PyTango.DebugIt()
    @attribute(name='LinePressure', unit='bar')
    def line_pressure(self):
        self.info_stream("read_LinePressure")
        return self.statusPacket.line_pressure

    @PyTango.DebugIt()
    @attribute(name='Alarm', dtype=str)
    def alarm(self):
        self.info_stream("read_Alarm")
        return self.statusPacket.alarm

    @PyTango.DebugIt()
    @attribute(name='RunTime', dtype=str)
    def run_time(self):
        self.info_stream("read_RunTime")
        result = '{}d, {}h, {}m'.format(self.statusPacket.run_days,
                                        self.statusPacket.run_hours,
                                        self.statusPacket.run_mins)
        return result

    @PyTango.DebugIt()
    @attribute(name='ControllerNr', dtype=int)
    def controller_number(self):
        self.info_stream("read_ControllerNumber")
        return self.statusPacket.controller_nb

    @PyTango.DebugIt()
    @attribute(name='SoftwareVersion', dtype=int)
    def software_version(self):
        self.info_stream("read_SoftwareVersion")
        return self.statusPacket.software_version

    @PyTango.DebugIt()
    @attribute(name='EvapAdjust', dtype=int)
    def evap_adjust(self):
        self.info_stream("read_EvapAdjust")
        return self.statusPacket.evap_adjust

    @PyTango.DebugIt()
    @attribute(name='TurboMode', dtype=bool)
    def turbo_mode(self):
        self.info_stream("read_TurboModet")
        flow = self.statusPacket.gas_flow
        phase = self.statusPacket.phase
        self.info_stream('flow: {} , phase: {}'.format(flow, phase))
        if flow > 5 and phase != "Cool":
            turbomode = True
        else:
            turbomode = False
        return turbomode

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


def main():
    OxfCryo700.run_server()


if __name__ == '__main__':
    main()
