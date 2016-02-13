<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "notifiers" %></%def>

<h1>Notifiers</h1>

After an alarm was raised notifications will be sent to inform the user about the alarm.

<%include file="angular_edit.mako" args="baseclass='notifiers', basetitle='Notifiers'" />


<h2>Parameters</h2>

<%include file="angular_edit.mako" args="baseclass='notifierparams', basetitle='Notifier Parameter', query_filter='object_type==\'notifier\''" />

