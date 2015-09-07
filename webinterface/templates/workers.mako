<%inherit file="main.mako"/>



<h1>Workers</h1>

A worker is a pi which listens on its GPIO Pins and sends alarms to the manager.


<%include file="angular_edit.mako" args="baseclass='workers', basetitle='Worker'" />

