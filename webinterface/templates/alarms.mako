<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "alarms" %></%def>

<h1>Alarms</h1>

<%include file="angular_edit.mako" args="baseclass='alarms', basetitle='Alarm'" />

<h1>Logs</h1>

<%include file="angular_edit.mako" args="baseclass='logs', basetitle='Log Entry'" />
