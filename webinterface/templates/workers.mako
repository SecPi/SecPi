<%inherit file="main.mako"/>

<%block name="subnav">
<%include file="subnav.mako" />
</%block>

<h1>Workers</h1>

A worker is a pi which listens on its GPIO Pins and sends alarms to the manager.

<div ng-controller="TestController as testi">
<div id="flash_message" ng-class="testi.flash_type" ng-show="testi.flash_message != null">
	{{testi.flash_message}}
</div>



<input type="button" ng-click="testi.getList()" value="get list" /> <br />

<table class="list" ng-show="testi.data.length > 0">
	<tr class="listheader">
		<th ng-repeat="(k, v) in testi.fields">{{v['name']}}</th>
		<th>&nbsp;</th><!-- for delete button -->
	</tr>
	<tr ng-repeat="obj in testi.data">
		<td ng-repeat="(k, v) in testi.fields">{{obj[k]}}</td>
		<td><a href="delete?id={{obj.id}}" onclick="return confirm('Are you sure?')"><img src="/static/img/icons/minus.png" alt="delete" title="delete" /></a><img src="/static/img/icons/edit.png" alt="edit" title="edit" ng-click="testi.showEdit($index)" /></td>
	</tr>
</table>

<div ng-show="testi.edit_data">
<form ng-submit="testi.saveEdit()">
	<table>
		<tr ng-repeat="(k, v) in testi.fields">
			<td>{{v['name']}}</td>
			<td><input type="text" name="k" id="k" ng-model="testi.edit_data[k]" /></td>
		</tr>
		<tr>
			<td>Submit</td>
			<td><input type="submit" value="Submit" /></td>
		</tr>
	</table>
</form>
</div>

</div>

