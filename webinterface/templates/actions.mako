<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "actions" %></%def>

<h1>Actions</h1>

An action is something a worker does, reacting on an alarm.

<%include file="angular_edit.mako" args="baseclass='actions', basetitle='Action'" />


<h2>Parameters</h2>

<%include file="angular_edit.mako" args="baseclass='actionparams', basetitle='ActionParams'" />

