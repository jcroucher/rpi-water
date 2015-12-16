#!/usr/bin/python
#
# Copyright (c) 2015 John Croucher www.jcroucher.com
# Licensed under the [MIT license](http://opensource.org/licenses/MIT).
#

import traceback
import sys

import core.Hardware
import core.Web


def main(argv):

    water = core.Hardware.ZoneProgramRunner()  # Raspberry pi hardware interface.
    webRunner = core.Web.WebRunner()  # Web admin system

    try:
        webRunner.start_web()
        water.main_loop()

    except KeyboardInterrupt:
        print("User requested quit")

    except Exception as e:
        print("Fatal error, quitting")
        s = traceback.format_exc()
        serr = "there were errors:\n%s\n" % (s)
        sys.stderr.write(serr)

    finally:
        water.cleanup()
        webRunner.cleanup()

if __name__ == '__main__':
    main(sys.argv)
