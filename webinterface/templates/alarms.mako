<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "alarms" %></%def>

<h1>Alarms</h1>
All the alarms that occur.

<%include file="angular_edit.mako" args="baseclass='alarms', basetitle='Alam'" />

<h1>Logs</h1>

<%include file="angular_edit.mako" args="baseclass='logs', basetitle='Log Entry'" />
