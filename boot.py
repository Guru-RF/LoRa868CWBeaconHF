import usb_cdc
import storage

usb_cdc.enable(console=True, data=True)

new_name = "LoraCwB"
storage.remount("/", readonly=False)
m = storage.getmount("/")
m.label = new_name
storage.remount("/", readonly=True)