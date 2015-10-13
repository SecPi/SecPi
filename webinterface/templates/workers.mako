<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "workers" %></%def>


<h1>Workers</h1>

A worker is a pi which listens on its GPIO Pins and sends alarms to the manager.


<%include file="angular_edit.mako" args="baseclass='workers', basetitle='Worker'" />


<h2>Workers <--> Actions</h2>
<%include file="rel.mako" args="leftclass='worker', leftname='Worker', rightclass='action', rightname='Actions'" />