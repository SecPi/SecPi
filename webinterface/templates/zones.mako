<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "zones" %></%def>

<h1>Zones</h1>

A zone is a combination of multiple sensors.

<%include file="angular_edit.mako" args="baseclass='zones', basetitle='Zone'" />
