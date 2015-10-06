<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "setups" %></%def>

<h1>Setups</h1>

A setup is a combination of zones.

<%include file="angular_edit.mako" args="baseclass='setups', basetitle='Setup'" />

<h1>Zones</h1>

A zone is a combination of multiple sensors.

<%include file="angular_edit.mako" args="baseclass='zones', basetitle='Zone'" />


<h1>Sensors</h1>
A sensor is a sensor attached to the Raspberry PIs GPIO Pins.

<%include file="angular_edit.mako" args="baseclass='sensors', basetitle='Sensor'" />


<h2>Parameters</h2>

<%include file="angular_edit.mako" args="baseclass='params', basetitle='Params', query_filter='object_type==\'sensor\''" />
