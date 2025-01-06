# micropython
# MIT license
# Copyright (c) 2023 Roman Shevchik
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, check_value
from sensor_pack_2.ioexpander import IOExpander, port_config_raw


# Please read this before use!: https://www.nxp.com/part/PCF8574T
# Представляет собой расширитель портов ввода вывода с управлением по шине i2c.
# Данная микросхема содержит только один(!) внутренний регистр.
# Provides general-purpose remote I/O expansion via the two-wire bidirectional I2C-bus.
# The devices consist of eight quasi-bidirectional ports.
class PCF8574(IOExpander):
    """Provides general-purpose remote I/O expansion via the two-wire bidirectional I2C-bus."""
    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x20):
        s0 = f"Invalid address value: 0x{address:x}!"
        if address < 0x38:  # PCF8574
            check_value(address, range(0x20, 0x28), s0)
        else:   # PCF8574A
            check_value(address, range(0x38, 0x40), s0)
        #
        super().__init__(port_count=1, port_width=8)
        self._device = DeviceEx(adapter, address, True)
        #
        self._setup()

    # PORT
    def get_port_value(self) -> int:
        """считывает значение на линиях P0..P7."""
        _dev = self._device
        return _dev.read_reg(reg_addr=_dev.address, bytes_count=1)[0]

    def set_port_value(self, value: int):
        """записывает значения на линии P0..P7."""
        _dev = self._device
        _dev.write_reg(reg_addr=_dev.address, value=value, bytes_count=1)

    # PORT RAW
    def set_port_config_raw(self, config: port_config_raw):
        """Записывает в соотв. регистры настройки(!) текущего активного порта значения в 'сыром' виде."""
        self.set_port_value(config.direction_reg)

    def get_port_config_raw(self) -> port_config_raw:
        """Возвращает содержимое регистров настройки(!) текущего активного порта в сыром виде."""
        return port_config_raw(direction_reg=self.get_port_value(), input_invert_reg=None, pull_reg=None)

    def _setup(self, value: int = 0xFF):
        """Настройка портов на ввод/вывод. По умолчанию выводы P0..P7 настраиваются как входы!
        Если бит установлен в ноль, то происходит "подтяжка" вывода порта P0..P7 к земле через внутренний транзистор!
        Если бит установлен в единицу, вывод порта P0..P7 будет подтянут к питанию через источник тока в 100 uA!

        Поэтому:
            * если вы подключаете к выводу порта P0..P7 кнопку, то записывайте в соотв. бит ЕДИНИЦУ и потом ЧИТАЙТЕ
              состояние, а кнопку подключайте между выводом порта и ЗЕМЛЕЙ(VSS)!!!
            * если вы подключаете к выводу порта P0..P7 нагрузку, то подавать напряжение на нее нужно ЗАПИСЬЮ в
              соответствующий бит НУЛЯ, а нагрузку подключайте между +Питание(VDD) и выводом порта P0..P7!!!"""
        self.set_port_value(value)
