<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "actionparams" %></%def>

<h1>Action Parameters</h1>

Parameteres that will be passed to the actions.

<%include file="angular_edit.mako" args="baseclass='actionparams', basetitle='Action Parameter'" />
