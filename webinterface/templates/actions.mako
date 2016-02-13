<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "actions" %></%def>

<h1>Actions</h1>

An action is executed after an alarm was raised.

<%include file="angular_edit.mako" args="baseclass='actions', basetitle='Action'" />


<h2>Parameters</h2>

<%include file="angular_edit.mako" args="baseclass='params', basetitle='Params', query_filter='object_type==\'action\''" />

