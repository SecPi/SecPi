<%inherit file="main.mako"/>

<%block name="subnav">
<%include file="subnav.mako" />
</%block>

<script type="text/javascript">
	var BASE_LINK = '/workers';
	var OBJ_TITLE = 'Worker'
</script>

<h1>Workers</h1>

A worker is a pi which listens on its GPIO Pins and sends alarms to the manager.


<%include file="angular_edit.mako" />

