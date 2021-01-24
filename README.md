# mfrc522

A python library to read/write RFID tags via the budget MFRC522 RFID module.

This code was published in relation to a [blog post](https://pimylifeup.com/raspberry-pi-rfid-rc522/) and you can find out more about how to hook up your MFRC reader to a Raspberry Pi there.

## Installation

Clone this repository and run `pip install .` in the top level directory.

## Example Code

The following code will read a tag from the MFRC522

```python
from time import sleep
import sys
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()

try:
    while True:
        print("Hold a tag near the reader")
        uid, text = reader.read()
        print("UID: {}\nText: {}".format(uid, text))
        sleep(5)
finally:
    GPIO.cleanup()
```

## Additional Resources

MIFARE Classic EV1 1K - Mainstream contactless smart cardIC for fast and easy solution development

https://www.nxp.com/docs/en/data-sheet/MF1S50YYX_V1.pdf
