# !/bin/bash
sudo cp -r  core __main__
sudo cp -r ../../xdevice/src/xdevice __main__/
sudo cp -r  __main__/*  /usr/bin
sudo chmod 777 /usr/bin/core/_init_global_config.py __main__/core __main__/xdevice
