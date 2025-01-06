"""Интерфейс расширителей ввода-вывода.
I/O expander interface."""

from collections import namedtuple
from sensor_pack_2.base_sensor import Iterator
from sensor_pack_2.base_sensor import check_value

_pin_config = "digital_input pull_up pull_down int_req_enable"
# digital_input - если бит в Истина(1), то вывод является дискретным входом, иначе дискретным выходом (обычно(!). Такие значения
# указаны страницах данных расширителей, но может быть иначе!)
# pull_up - если бит в Истина(1), то вывод подтянут к напряжению питания микросхемы +Vcc (читайте даташит на микросхему!).
# pull_down - если бит в Истина(1), то вывод подтянут к GND (читайте даташит на микросхему!).
# int_req_enable - если бит в Истина(1), то вывод вызывает прерывание
pin_config = namedtuple("pin_config", _pin_config)

_port_info = "count width"
port_info = namedtuple("port_info", _port_info)

# _port_config_raw = "direction_reg input_invert_reg int_on_change_reg pull_reg"
_port_config_raw = "direction_reg input_invert_reg pull_reg"
# содержит значения(!) соответствующих регистров
# direction_reg - настройки выводов микросхемы, соответствующих разрядам порта, как вход (DI) или выход (DO).
# input_invert_reg - инверсия, для вывода, настроенного, как вход(!). Значение для каждой микросхемы индивидуально.
# pull_reg - подтяжка вывода к Vcc или GND, значение для каждой микросхемы индивидуально.
# int_on_change_reg - настройка генерации прерывания микросхемой-расширителем при изменении состояния входа/входов (DI)
port_config_raw = namedtuple("port_config_raw", _port_config_raw)
# содержит адреса(!) соответствующих регистров в адресном пространстве расширителя ввода-вывода
# direction_reg - адрес регистра настройки направления выводов микросхемы, как вход (DI) или выход (DO).
# invert_reg - адрес регистра инверсии, для выводов, настроенного, как вход(!).
# pull_reg - адрес регистра подтяжки вывода к Vcc или GND, значение для каждой микросхемы индивидуально.
# int_on_change_reg - адрес регистра настройки генерации прерывания микросхемой-расширителем при изменении состояния входа/входов (DI)
port_config_addr = namedtuple("port_config_addr", _port_config_raw)

class IOExpander(Iterator):
    """Расширитель ввода-вывода. Общий интерфейс. I/O Expander. Common Interface."""

    def __init__(self, port_count: int = 2, port_width : int = 8):
        self._port_count = port_count
        self._port_width = port_width
        self._active_port = 0

    def _check_port_numb(self, n_port: int) -> int:
        """Проверяет номер порта на правильность"""
        check_value(n_port, range(self._port_count), f"Неверный номер порта: {n_port}")
        return n_port

    def _check_pin_numb(self, n_pin: int) -> int:
        """Проверяет номер вывода порта на правильность"""
        check_value(n_pin, range(self._port_width), f"Неверный номер вывода/pin: {n_pin}")
        return n_pin

    # PORT
    def set_active_port(self, n_port : int):
        """Устанавливает текущий активный порт расширителя"""
        self._check_port_numb(n_port)
        self._active_port = n_port

    def get_port_count(self) -> int:
        """Возвращает количество портов ввода-вывода"""
        return self._port_count

    def get_active_port(self) -> int:
        """Возвращает текущий активный порт расширителя"""
        return self._active_port

    def get_port_info(self) -> port_info:
        """Возвращает информацию о порте ввода-вывода."""
        return port_info(count=self._port_count, width=self._port_width)

    def get_port_value(self) -> int:
        """Возвращает содержимое регистра порта ввода(DI)). Для переопределения в наследниках!"""
        raise NotImplemented

    def set_port_value(self, value: int):
        """Устанавливает содержимое регистра порта вывода(DO). Для переопределения в наследниках!"""
        raise NotImplemented

    # PORT RAW
    def set_port_config_raw(self, config: port_config_raw):
        """Записывает в соотв. регистры настройки(!) текущего активного порта значения в 'сыром' виде.
        Для переопределения в наследниках!"""
        raise NotImplemented

    def get_port_config_raw(self) -> port_config_raw:
        """Возвращает содержимое регистров настройки(!) текущего активного порта в сыром виде.
        Для переопределения в наследниках!"""
        raise NotImplemented

    # Iterator methods. Методы для итератора.
    def __iter__(self):
        return self

    def __next__(self):
        return self.get_port_value()


    class IOExpanderPin:
        """Расширитель ввода-вывода с возможностью работы с отдельными выводами/пинами портов."""
    # PIN
    def get_pin_config(self, n_pin: int) -> pin_config:
        """Возвращает настройку вывода n_pin текущего активного порта. Для переопределения в наследниках!"""
        raise NotImplemented

    def set_pin_config(self, n_pin: int, cfg: pin_config):
        """Устанавливает настройку вывода n_pin текущего активного порта. Для переопределения в наследниках!"""
        raise NotImplemented

    def get_pin_value(self, n_pin: int) -> bool:
        """Возвращает значение на выводе n_pin текущего активного порта. Для переопределения в наследниках!"""
        raise NotImplemented

    def set_pin_value(self, n_pin: int, val: bool) -> int:
        """Устанавливает значение на выводе n_pin текущего активного порта. Для переопределения в наследниках!"""
        raise NotImplemented