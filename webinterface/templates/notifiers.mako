<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "notifiers" %></%def>

<h1>Notifiers</h1>

A notification will be sent with these settings.

<%include file="angular_edit.mako" args="baseclass='notifiers', basetitle='Notifiers'" />


<h2>Parameters</h2>

<%include file="angular_edit.mako" args="baseclass='params', basetitle='Params', query_filter='object_type==\'notifier\''" />

