<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "logs" %></%def>

<h1>Log Entries</h1>

All the logging stuff.

<%include file="angular_edit.mako" args="baseclass='logs', basetitle='Log Entry'" />
