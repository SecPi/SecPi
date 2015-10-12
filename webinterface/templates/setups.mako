<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "setups" %></%def>

<h1>Setups</h1>

A setup is a combination of zones.

<%include file="angular_edit.mako" args="baseclass='setups', basetitle='Setup'" />

<h1>Setups <--> Zones</h1>
<div ng-controller="SetupsZonesController as szCtrl">
	<table class="list">
		<tr>
			<th>Setup</th>
			<th>Zones</th>
			<th><img src="/static/img/icons/plus.png" ng-click="szCtrl.showAdd()" /></th>
		</tr>
		<tr ng-repeat="obj in szCtrl.setups_zones">
			<td>{{obj['name']}}</td>
			<td><p ng-repeat="z in obj['zones']">{{z.name}} <img src="/static/img/icons/minus.png" alt="delete" title="delete" ng-click="szCtrl.delete(obj.id, z.id)" /></p></td>
			<td></td>
		</tr>
	</table>
	
	<div id="sz-form" title="Add">
		Setup: <select name="setup" id="setup"
			ng-options="sup.name for sup in szCtrl.setups track by sup.id"
			ng-model="szCtrl.setup"></select><br />
		Zone: <select name="zone" id="zone"
			ng-options="zo.name for zo in szCtrl.zones track by zo.id"
			ng-model="szCtrl.zone"></select>
	</div>
</div>


<h1>Zones</h1>

A zone is a combination of multiple sensors.

<%include file="angular_edit.mako" args="baseclass='zones', basetitle='Zone'" />


<h1>Sensors</h1>
A sensor is a sensor attached to the Raspberry PIs GPIO Pins.

<%include file="angular_edit.mako" args="baseclass='sensors', basetitle='Sensor'" />


<h2>Parameters</h2>

<%include file="angular_edit.mako" args="baseclass='params', basetitle='Params', query_filter='object_type==\'sensor\''" />
