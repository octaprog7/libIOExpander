"""PCA9555 и TCA9555 I2C IO-Expander/Расширители ввода-вывода"""

from sensor_pack_2.bus_service import BusAdapter
from sensor_pack_2.base_sensor import DeviceEx
from sensor_pack_2.ioexpander import IOExpander, port_config_raw, port_config_addr
from sensor_pack_2.base_sensor import check_value


class XCA9555(IOExpander):
    """Класс, управляющий I2C IO-Expander. Чип генерирует прерывания при любом изменении состояния цифровых ВХОДОВ!
    Class that controls I2C IO-Expander. The chip generates interrupts on any change in the state of digital INPUTS!"""

    def __init__(self, adapter: BusAdapter, address=0x20):
        check_value(address, range(0x20, 0x28), f"Неверное значение адреса I2C устройства: 0x{address:x}")
        super().__init__(port_count=2, port_width=8)
        self._device = DeviceEx(adapter, address, True)

    def _get_io_port_addr(self, n_port: int, op_read: bool = True) -> int:
        """Возвращает адрес порта ввода-вывода по его номеру и операции.
        Если op_read Истина, то производится чтение, иначе Запись."""
        self._check_port_numb(n_port)
        if op_read:
            return n_port
        # op_read is False (writing)
        return 2 + n_port

    def _get_config_addr(self, n_port: int) -> port_config_addr:
        """Возвращает адрес порта настройки/конфигурации в адресном пространстве расширителя ввода-вывода"""
        self._check_port_numb(n_port)
        return port_config_addr(direction_reg=6 + n_port, input_invert_reg=4 + n_port, pull_reg=None)

    # IOExpander

    def get_port_value(self) -> int:
        """Возвращает содержимое регистра ввода(DI))"""
        n_port = self.get_active_port()
        addr = self._get_io_port_addr(n_port=n_port, op_read=True)
        raw = self._device.read_reg(reg_addr=addr, bytes_count=1)
        return raw[0]

    def set_port_value(self, value: int):
        """Устанавливает содержимое регистра порта вывода(DO)"""
        n_port = self.get_active_port()
        addr = self._get_io_port_addr(n_port=n_port, op_read=False)
        self._device.write_reg(reg_addr=addr, value=value, bytes_count=1)

    def set_port_config_raw(self, config: port_config_raw):
        """Записывает в соотв. регистры настройки(!) текущего активного порта значения в 'сыром' виде."""
        n_port = self.get_active_port()
        cfg_addr = self._get_config_addr(n_port)
        # print(f"cfg_addr: {cfg_addr}")
        _write_reg = self._device.write_reg
        if not config.direction_reg is None:
            _write_reg(reg_addr=cfg_addr.direction_reg, value=config.direction_reg, bytes_count=1)
        if not config.input_invert_reg is None:
            _write_reg(reg_addr=cfg_addr.input_invert_reg, value=config.input_invert_reg, bytes_count=1)

    def get_port_config_raw(self) -> port_config_raw:
        """Возвращает содержимое регистров настройки(!) текущего активного порта в сыром виде."""
        n_port = self.get_active_port()
        cfg_addr = self._get_config_addr(n_port)
        _read_reg = self._device.read_reg
        #
        _dir = _read_reg(reg_addr=cfg_addr.direction_reg, bytes_count=1)[0]
        _inv = _read_reg(reg_addr=cfg_addr.input_invert_reg, bytes_count=1)[0]
        #
        return port_config_raw(direction_reg=_dir, input_invert_reg=_inv, pull_reg=None)

