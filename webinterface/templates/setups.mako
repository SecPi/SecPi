<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "setups" %></%def>

<h1>Setups</h1>

A setup consists of one or multiple zones which should be monitored.

<%include file="angular_edit.mako" args="baseclass='setups', basetitle='Setup'" />

<h2>Setups <--> Zones</h2>
<%include file="rel.mako" args="leftclass='setup', leftname='Setup', rightclass='zone', rightname='Zone'" />

<h1>Zones</h1>

A zone is an area which contains a certain amounts of sensors.

<%include file="angular_edit.mako" args="baseclass='zones', basetitle='Zone'" />


<h1>Sensors</h1>

Sensors are monitoring a certain area, they will raise an alarm if something is out of the ordinary.

<%include file="angular_edit.mako" args="baseclass='sensors', basetitle='Sensor'" />


<h2>Parameters</h2>

<%include file="angular_edit.mako" args="baseclass='params', basetitle='Params', query_filter='object_type==\'sensor\''" />
