<%inherit file="main.mako"/>

<%block name="subnav">
<%include file="subnav.mako" />
</%block>

<h1>Workers</h1>

A worker is a pi which listens on its GPIO Pins and sends alarms to the manager.