import threading
import serial
from tango import DevState
from tango.server import Device, attribute, command
from tango.server import device_property
from .oxfordcryo import StatusPacket, CSCOMMAND, splitBytes


class OxfCryo700(Device):
    port = device_property(dtype=str, doc='Serial port name (/dev/ttyXX)')

    def init_device(self):
        Device.init_device(self)
        self.info_stream('In Python init_device method')
        self.serial = serial.Serial(self.port)
        self.status_packet = None
        self.status_thread = threading.Thread(group=None,
                                              target=self.update_status_packet)
        self.status_thread_stop = threading.Event()
        self.status_thread.start()
        self.set_state(DevState.ON)

    def delete_device(self):
        self.status_thread_stop.set()
        self.status_thread.join(3.0)
        self.info_stream('OxfCryo700.delete_device')

    def _write(self, data):
        data_bytes = bytes(data)
        self.serial.write(data_bytes)
    # ------------------------------------------------------------------
    # COMMANDS
    # ------------------------------------------------------------------

    @command
    def Restart(self):
        data = [2, CSCOMMAND.RESTART]
        self.debug_stream("Restart(): sending data: {}".format(data))
        self._write(data)

    @command
    def Purge(self):
        data = [2, CSCOMMAND.PURGE]
        self.debug_stream("PURGE(): sending data: {}".format(data))
        self._write(data)

    @command
    def Stop(self):
        data = [2, CSCOMMAND.STOP]
        self.debug_stream("Stop(): sending data: {}".format(data))
        self._write(data)

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
        data = [6, CSCOMMAND.RAMP, rateHigh, rateLow, finalTempHigh,
                finalTempLow]
        self.debug_stream("Ramp(): sending data: {}".format(data))
        self._write(data)

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
        data = [3, CSCOMMAND.TURBO, turboState]
        self.debug_stream("Turbo(): sending data: {}".format(data))
        self._write(data)

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
        data = [4, CSCOMMAND.COOL, HIBYTE, LOBYTE]
        self.debug_stream("Cool(): sending data: {}".format(data))
        self._write(data)

    @command
    def Pause(self):
        data = [2, CSCOMMAND.PAUSE]
        self.debug_stream("Pause(): sending data:{}".format(data))
        self._write(data)

    @command
    def Resume(self):
        data = [2, CSCOMMAND.RESUME]
        self.debug_stream("Resume(): sending data: {}".format(data))
        self._write(data)

    @command(dtype_in=int, doc_in='Plat command identifier - parameter '
                                  'follows')
    def Plat(self, val):
        """
        The CSCOMMAND_PLAT command packet, size = 4
        The Params[] array consists of a short containing the duration of the
        Plat in minutes
        """

        HIBYTE, LOBYTE = splitBytes(val)
        data = [4, CSCOMMAND.PLAT, HIBYTE, LOBYTE]
        self.debug_stream("Plat(): sending data: {}".format(data))
        self.serial.write(data)

    @command(dtype_in=int, doc_in='End command identifier - parameter follows')
    def End(self, val):
        """
        The CSCOMMAND_END command packet, size = 4
        The Params[] array consists of a short containing desired ramp rate
        in K/hour
        """

        HIBYTE, LOBYTE = splitBytes(val)
        data = [4, CSCOMMAND.END, HIBYTE, LOBYTE]
        self.debug_stream("End(): sending data: {}".format(data))
        self.serial.write(data)

    # Command without description on the manual. It is not used on the
    # beamlines
    # @command(dtype_in=float, doc_in='Shyt the Cryosutter for the specified '
    #                                 'length of time.')
    # def CryoShutter_Start_Auto(self, value):
    #     """
    #     The CSCOMMAND_CRYOSHUTTER_START_AUTO command packet, size = 3
    #     The Params[] array consists of a short containing the duration of the
    #     anneal time in tenths of a second
    #     """
    #     val = int(value * 10)
    #     data = [3, CSCOMMAND.CRYOSHUTTER_START_AUTO, val]
    #     self.debug_stream("CryoShutter_Start_Auto(): "
    #                       "sending data: {}".format(data))
    #     self.serial.write(data)

    @command
    def CryoShutter_Start_Man(self):
        """
        The	CSCOMMAND_CRYOSHUTTER_START_MAN command packet, size = 2
        Shut until CSCOMMAND_CRYOSHUTTER_STOP
        """
        data = [2, CSCOMMAND.CRYOSHUTTER_START_MAN]
        self.debug_stream("CryoShutter_Start_Man(): "
                          "sending data: {}".format(data))
        self.serial.write(data)

    @command
    def CryoShutter_Stop(self):
        """
        The	CSCOMMAND_CRYOSHUTTER_STOP command packet, size = 2
        Open the CryoShutter
        """
        data = [2, CSCOMMAND.CRYOSHUTTER_STOP]
        self.debug_stream("CryoShutter_Stop(): "
                          "sending data: {}".format(data))
        self.serial.write(data)

    @command(dtype_in=int, doc_in='Set status packet format: 0 old, '
                                  '1 extended')
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
        except Exception:
            raise Exception(
                "Wrong type of arguments. Status_Format must be an integer, "
                "0 or 1.")

        data = [3, CSCOMMAND.SETSTATUSFORMAT, val]
        self.debug_stream("Status_Format(): "
                          "sending data: {}".format(data))
        self.serial.write(data)

    # ------------------------------------------------------------------
    # ATTRIBUTES
    # ------------------------------------------------------------------

    @attribute(name='GasSetPoint', unit='K')
    def gas_set_point(self):
        self.info_stream("read_GasSetPoint")
        return self.status_packet.gas_set_point

    @attribute(name='GasTemp', unit='K')
    def gas_temp(self):
        self.info_stream("read_GasSetPoint")
        return self.status_packet.gas_temp

    @attribute(name='GasError', unit='K')
    def gas_error(self):
        self.info_stream("read_GasError")
        return self.status_packet.gas_error

    @attribute(name='RunMode', dtype=str)
    def run_mode(self):
        self.info_stream("read_RunMode")
        return self.status_packet.run_mode

    @attribute(name='Phase', dtype=str)
    def phase(self):
        self.info_stream("read_Phase")
        return self.status_packet.phase

    @attribute(name='RampRate', dtype=int)
    def ramp_rate(self):
        self.info_stream("read_RampRate")
        return self.status_packet.ramp_rate

    @attribute(name='TargetTemp')
    def target_temp(self):
        self.info_stream("read_TargetTemp")
        return self.status_packet.target_temp

    @attribute(name='EvapTemp', unit='K')
    def evap_temp(self):
        self.info_stream("read_EvapTemp")
        return self.status_packet.evap_temp

    @attribute(name='SuctTemp', unit='K')
    def suct_temp(self):
        self.info_stream("read_SuctTemp")
        return self.status_packet.suct_temp

    @attribute(name='GasFlow', unit='l/min')
    def gas_flow(self):
        self.info_stream("read_GasFlow")
        return self.status_packet.gas_flow

    @attribute(name='GasHeat', unit='%')
    def gas_heat(self):
        self.info_stream("read_GasHeat")
        return self.status_packet.gas_heat

    @attribute(name='EvapHeat', unit='%')
    def evap_heat(self):
        self.info_stream("read_EvapHeat")
        return self.status_packet.evap_heat

    @attribute(name='SuctHeat', unit='%')
    def suct_heat(self):
        self.info_stream("read_SuctHeat")
        return self.status_packet.suct_heat

    @attribute(name='LinePressure', unit='bar')
    def line_pressure(self):
        self.info_stream("read_LinePressure")
        return self.status_packet.line_pressure

    @attribute(name='Alarm', dtype=str)
    def alarm(self):
        self.info_stream("read_Alarm")
        return self.status_packet.alarm

    @attribute(name='RunTime', dtype=str)
    def run_time(self):
        self.info_stream("read_RunTime")
        result = '{}d, {}h, {}m'.format(self.status_packet.run_days,
                                        self.status_packet.run_hours,
                                        self.status_packet.run_mins)
        return result

    @attribute(name='ControllerNr', dtype=int)
    def controller_number(self):
        self.info_stream("read_ControllerNumber")
        return self.status_packet.controller_nb

    @attribute(name='SoftwareVersion', dtype=int)
    def software_version(self):
        self.info_stream("read_SoftwareVersion")
        return self.status_packet.software_version

    @attribute(name='EvapAdjust', dtype=int)
    def evap_adjust(self):
        self.info_stream("read_EvapAdjust")
        return self.status_packet.evap_adjust

    @attribute(name='TurboMode', dtype=bool)
    def turbo_mode(self):
        self.info_stream("read_TurboMode")
        flow = self.status_packet.gas_flow
        phase = self.status_packet.phase
        self.info_stream('flow: {} , phase: {}'.format(flow, phase))
        if flow > 5 and phase != "Cool":
            turbomode = True
        else:
            turbomode = False
        return turbomode

    def update_status_packet(self):
        self.status_thread_stop.clear()
        # flushing input buffer
        self.flush_input_buffer()
        # updating loop
        while not self.status_thread_stop.isSet():
            # TODO Implement check of the status format package it can be
            #  extended
            raw_data = self.serial.read(32)
            if self.serial.inWaiting() > 32:
                # if there are newer packets in the buffer, we do not process
                # and just continue
                continue
            data = list(map(int, raw_data))
            try:
                self.status_packet = StatusPacket(data)
            except Exception as e:
                self.error_stream("Error while parsing read data: %s" % e)
                self.error_stream("Flushing input buffer to start from "
                                  "the skratch")
                self.flush_input_buffer()

    def flush_input_buffer(self):
        while self.serial.inWaiting() > 0:
            self.serial.flushInput()


def main():
    OxfCryo700.run_server()


if __name__ == '__main__':
    main()
