<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "sensors" %></%def>

<h1>Sensors</h1>
A sensor is a sensor attached to the Raspberry PIs GPIO Pins.

<%include file="angular_edit.mako" args="baseclass='sensors', basetitle='Sensor'" />

