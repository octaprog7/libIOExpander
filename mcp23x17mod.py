"""MCP23x17 I2C/SPI IO-Expander/Расширитель ввода-вывода"""

import micropython
from machine import Pin
from sensor_pack_2 import bus_service
from sensor_pack_2.ioexpander import IOExpander, port_config_raw
from sensor_pack_2.base_sensor import DeviceEx, check_value

from collections import namedtuple

int_cfg_fields = "gp_int_en dev_val int_con"
int_cfg_raw_23x17 = namedtuple("int_cfg_raw_23x17", int_cfg_fields)
if_cap_23x17 = namedtuple("if_cap_23x17", "int_flag int_cap")

class MCP23x17(IOExpander):
    """MicroPython class for control 16-Bit I/O Expander with Serial Interface"""

    def __init__(self, adapter: bus_service.BusAdapter, address: [int, Pin] = 0x27):
        """eight_bit_mode - если Истина, то два порта (8-бит) ввода/вывода работают отдельно друг от друга.
        Иначе, два порта (8-бит) ввода/вывода объединяются в один (16 бит) порт ввода/вывода"""
        s0 = f"Invalid address value: 0x{address:x}!"
        check_value(address, range(0x20, 0x28), s0)
        # DeviceEx.__init__(self, adapter, address, big_byte_order=True)
        super().__init__(port_count=2, port_width=8)
        self._device = DeviceEx(adapter, address, big_byte_order=True)
        # после POR IOCON.BANK = 0 всегда!
        self._bank = self._get_addr_mode()  # то же самое, что и IOCON.BANK. После POR он в нуле!
        # Регистры, связанные с каждым портом, разделены на разные банки.
        # Вывод INTA связан только с PORTA, а вывод INTB связан только с PORTB.
        # Последовательные операции чтения/записи отключены, указатель адреса автоматически не увеличивается.
        self._setup_iocon(bank=True, mirror=False, seqop=True)
        self._bank = self._get_addr_mode()

    @micropython.native
    def _get_reg_address(self, index: int) -> (int, int):
        """
        Возвращает адреса пар(!) регистров по их индексу 0..10 в виде кортежа (адрес регистра А, адрес регистра Б)
        index,  REG
        0       IODIR
        1       IPOL
        2       GPINTEN
        3       DEFVAL
        4       INTCON
        5       IOCON
        6       GPPU
        7       INTF
        8       INTCAP
        9       GPIO
        10      OLAT

        :param index:
        :return:
        """
        s0 = f"Invalid index value: {index}!"
        check_value(index, range(11), s0)
        if self._is_16_bit_mode():
            x = index << 1
            return x, x + 1
        # 8 bit mode
        x = index
        return x, x + 0x10

    def _read_reg_by_index(self, index: int) -> int:
        """Чтение регистра по его индексу и текущему активному порту"""
        addr = self._get_reg_address(index)[self.get_active_port()]    #
        bytes_count = 2 if self._is_16_bit_mode() else 1  # кол-во байт
        _dev = self._device
        res = _dev.read_reg(addr, bytes_count)  # bytes
        fmt = "H" if self._is_16_bit_mode() else "B"  # формат (H - unsigned short/B - unsigned byte)
        return _dev.unpack(fmt, res)[0]

    def _write_reg_by_index(self, index: int, value: int):
        """Запись в регистр по его индексу и текущему активному порту"""
        addr = self._get_reg_address(index)[self.get_active_port()]  #
        bytes_count = 2 if self._is_16_bit_mode() else 1  # кол-во байт
        self._device.write_reg(addr, value, bytes_count)

    # IOExpander

    def get_port_value(self) -> int:
        """Возвращает содержимое регистра порта ввода(DI))"""
        return self._read_reg_by_index(9)

    def set_port_value(self, value: int):
        """Устанавливает содержимое регистра порта вывода(DO)"""
        self._write_reg_by_index(9, value)

    # PORT RAW
    def set_port_config_raw(self, config: port_config_raw):
        """Записывает в соотв. регистры настройки(!) текущего активного порта значения в 'сыром' виде."""
        _wr_reg_by_index = self._write_reg_by_index
        if not config.direction_reg is None:
            _wr_reg_by_index(index=0, value=config.direction_reg)
        if not config.input_invert_reg is None:
            _wr_reg_by_index(index=1, value=config.input_invert_reg)
        if not config.pull_reg is None:
            _wr_reg_by_index(index=6, value=config.pull_reg)

    def get_port_config_raw(self) -> port_config_raw:
        """Возвращает содержимое регистров настройки(!) текущего активного порта в сыром виде."""
        _get_reg_by_index = self._read_reg_by_index
        _dir = _get_reg_by_index(0)
        _inv = _get_reg_by_index(1)
        _pull = _get_reg_by_index(6)
        #
        return port_config_raw(direction_reg=_dir, input_invert_reg=_inv, pull_reg=_pull)

    # END IOExpander

    def _get_addr_mode(self) -> bool:
        """Возвращает текущую адресацию регистров расширителя.
        Возвращает True, когда адресация портов раздельная (2 порта по 8 бит, IOCON.BANK = 1).
        Или False, когда адресация портов совместная (1 порт 16 бит, IOCON.BANK = 0)"""
        pair_of_addresses = (0x0A, 0x0B), (0x05, 0x15)      # адреса IOCON
        lst = list()
        _dev = self._device
        for pair in pair_of_addresses:
            for adr in pair:    # младший бит (бит 0) не доступен для записи в IOCON. Читается всегда, как 0!
                raw = _dev.read_reg(adr)
                _dev.write_reg(adr, raw[0] | 0x03, bytes_count=1)     # пишу в биты 0 и 1 единицу
                lst.append(_dev.read_reg(adr)[0] & 0x01)     # читаю два бита (0 и 1)
        #
        for i in (0, 2):
            if 0 == lst[i] == lst[i+1]:
                return i != 0       # если в младших битах нули, а я выше писал в них единицы, то это IOCON!
        return False

    @micropython.native
    def _is_16_bit_mode(self) -> bool:
        """Возвращает Истина, когда 16-ти битный режим включен. Один порт на 16 бит I/O!
        Иначе, два порта по 8 бит I/O"""
        return not self._bank

    # Уникальные(!) для этой микросхемы, методы

    def get_output_latch(self) -> int:
        """Возвращает значение OLAT.
        Регистр OLAT обеспечивает доступ к вывода"""
        return self._read_reg_by_index(0x0A)     # 0x0A - OLAT

    def set_output_latch(self, value: int):
        """Записывает значение в OLAT"""
        self._write_reg_by_index(0x0A, value)  # 0x0A - OLAT

    def get_if_cap(self) -> if_cap_23x17:
        """Возвращает содержимое регистров: INTERRUPT FLAG REGISTER, """
        _get_reg_by_index = self._read_reg_by_index
        #
        _int_f = _get_reg_by_index(7)     # INTERRUPT FLAG REGISTER
        _int_cap = _get_reg_by_index(8)   # INTCAP (INTERRUPT CAPTURED VALUE FOR PORT REGISTER)
        #
        return if_cap_23x17(int_flag=_int_f, int_cap=_int_cap)

    def _setup_iocon(self, bank: bool, mirror: bool = False,
                     seqop: bool = False, disslw: bool = False,
                     haen: bool = False, odr: bool= False, intpol: bool = False):
        """Setup IOCON register. Биты  HAEN, ODR, INTPOL обнуляю всегда!
        Вызывать только после(!) вызова _get_addr_mode()."""
        val = (bank << 7) | (mirror << 6) | (seqop << 5) | (disslw << 4) | (haen << 3) | (odr << 2) | (intpol << 1)
        _dev = self._device
        if not self._bank and bank:		# переход из 0 -> 1 (плоская адресация -> раздельная адресация)
            _dev.write_reg(0x0A, value=val, bytes_count=1)
            # self._write_reg(0x0A, value=(val << 8) | val, bytes_count=2)
            # self._write_reg(0x0B, value=val)
        if not bank and self._bank:		# переход из 1 -> 0 (раздельная адресация -> плоская адресация)
            _dev.write_reg(0x05, value=val, bytes_count=1)
            # self._write_reg(0x15, value=val)
        self._bank = bank

    def set_int_config(self, gp_int_en: [int, None], int_con: [int, None], def_val: [int, None]):
        """Настройка условий возникновения аппаратных прерывания текущего активного порта.
        gp_int_en - значение для регистра GPINTEN; def_val - значение для регистра DEFVAL; int_con - значение для регистра INTCON;"""
        _wr_reg_by_index = self._write_reg_by_index
        #
        if not gp_int_en is None:
            _wr_reg_by_index(index=2, value=gp_int_en)
        if not int_con is None:
            _wr_reg_by_index(index=4, value=int_con)
        if not def_val is None:
            _wr_reg_by_index(index=3, value=def_val)


    def get_int_config(self) -> int_cfg_raw_23x17:
        """Возвращает содержимое регистров настройки прерываний текущего активного порта."""
        #
        _get_reg_by_index = self._read_reg_by_index
        _int_en = _get_reg_by_index(2)
        _def_val = _get_reg_by_index(3)
        _int_con = _get_reg_by_index(4)
        #
        return int_cfg_raw_23x17(gp_int_en=_int_en, dev_val=_def_val, int_con=_int_con)
