# MicroPython
# MIT license
"""IO-Expander demo"""
import time
# import sys

from machine import I2C, Pin
from sensor_pack_2.bus_service import I2cAdapter
from sensor_pack_2.ioexpander import port_config_raw, IOExpander
from xca9555mod import XCA9555
from mcp23x17mod import MCP23x17
from pcf8574mod import PCF8574

# Пожалуйста, прочитайте документацию на MCP23017, PCA9555, PCF8574!
# Please read the MCP23017, PCA9555, PCF8574 documentation!

if __name__ == '__main__':
    # пожалуйста установите выводы scl и sda в конструкторе для вашей платы, иначе ничего не заработает!
    # please set scl and sda pins for your board, otherwise nothing will work!
    # https://docs.micropython.org/en/latest/library/machine.I2C.html#machine-i2c
    # i2c = I2C(id=1, scl=Pin(27), sda=Pin(26), freq=400_000)  # on Arduino Nano RP2040 Connect and Pico W tested!
    # i2c = I2C(id=1, scl=Pin(7), sda=Pin(6), freq=400_000)  # create I2C peripheral at frequency of 400kHz
    i2c = I2C(id=1, scl=Pin(7), sda=Pin(6), freq=400_000)
    adapter = I2cAdapter(i2c)       # адаптер для стандартного доступа к шине
    # Для проверки только одна из трех строк ниже должна быть без символа # комментария! For test only one of the three lines below should be without the # comment symbol!
    io_expander : IOExpander = XCA9555(adapter)
    # io_expander : IOExpander = MCP23x17(adapter)
    # io_expander : IOExpander = PCF8574(adapter=adapter, address=0x20)
    print(io_expander.__class__.__name__)
    val = io_expander.get_port_value()
    print("Информация о портах ввода-вывода. Information about input/output ports.")
    for n_port in range(2):
        print(16 * "-")
        io_expander.set_active_port(0)
        print(f"get_active_port: {io_expander.get_active_port()}")
        config = io_expander.get_port_config_raw()
        print(f"port_info: {config}")
        print(f"get_port_value: 0x{val:x}")

    print(16 * "-")
    io_expander.set_active_port(0)
    # настраиваю все биты порта 0, как ВЫХоды! I configure all bits of port 0 as OUTPUTS!
    config = port_config_raw(direction_reg=0, input_invert_reg=None, pull_reg=None)
    io_expander.set_port_config_raw(config)
    config = io_expander.get_port_config_raw()
    print(f"port_info: {config}")
    print(f"get_port_value: 0x{val:x}")
    
    print("Мигание светодиодами (СИД). Blinking of light-emitting diodes (LEDs).")
    for _ in range(10):
        io_expander.set_port_value(0x00)
        time.sleep_ms(200)
        io_expander.set_port_value(0xFF)
        time.sleep_ms(200)


    io_expander.set_active_port(1)
    config = port_config_raw(direction_reg=0xFF, input_invert_reg=0x00, pull_reg=0xFF)
    # настраиваю все биты порта 1, как ВХоды без инверсии! I configure all bits of port 1 as Inputs without inversion!
    io_expander.set_port_config_raw(config)
    
    # sys.exit(0)
    print(f"Состояние порта. Port status.")
    for _ in range(10):
        time.sleep_ms(200)
        val = io_expander.get_port_value()
        print(f"port_value: 0x{val:x}")