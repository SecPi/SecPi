<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "setups" %></%def>

<h1>Setups</h1>

A setup is a combination of zones.

<%include file="angular_edit.mako" args="baseclass='setups', basetitle='Setup'" />
