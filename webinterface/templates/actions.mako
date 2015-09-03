<%inherit file="main.mako"/>

<%block name="subnav">
<%include file="subnav.mako" />
</%block>

<script type="text/javascript">
	var BASE_LINK = '/actions';
	var OBJ_TITLE = 'Action'
</script>

<h1>Actions</h1>

An action is something a worker does, reacting on an alarm.

<%include file="angular_edit.mako" />

