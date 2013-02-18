hdmi-sniff
==========

HDMI DDC (I2C) inspection tool

Latest version:

  https://github.com/ApertureLabsLtd/hdmi-sniff

This tool is designed to demonstrate just how easy it is to recover HDCP crypto
keys from HDMI devices, but it could be extended to decode all data passed over
the I2C interface, such as MCCS, EDID, etc. You'll need an HDMI breakout cable
(how to make one is described in the blog entry below), and a Bus Pirate:

  http://dangerousprototypes.com/docs/Bus_Pirate

You'll also need a copy of Rich Wareham's hdcp-genkey to convert the sniffed KSV
to a key:

  https://github.com/rjw57/hdcp-genkey

For a walked through example, read this:

  http://adamsblog.aperturelabs.com/2013/02/hdcp-is-dead-long-live-hdcp-peek-into.html

Enjoy!
Adam

