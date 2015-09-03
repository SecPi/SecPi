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

<div ng-controller="DataController as dataCtrl">
<div id="flash_message" ng-class="dataCtrl.flash_type" ng-show="dataCtrl.flash_message != null">
	{{dataCtrl.flash_message}}
</div>

<pre>
{{dataCtrl.data}}
</pre>


<input type="button" ng-click="dataCtrl.getList()" value="get list" /> <br />

<table class="list" ng-show="dataCtrl.data.length > 0">
	<tr class="listheader">
		<th ng-repeat="(k, v) in dataCtrl.getFields('list')">{{v['name']}}</th>
		<th>&nbsp;</th><!-- for delete button -->
	</tr>
	<tr ng-repeat="obj in dataCtrl.data">
		<td ng-repeat="(k, v) in dataCtrl.fields">{{obj[k]}}</td>
		<td><a href="delete?id={{obj.id}}" onclick="return confirm('Are you sure?')"><img src="/static/img/icons/minus.png" alt="delete" title="delete" /></a><img src="/static/img/icons/edit.png" alt="edit" title="edit" ng-click="dataCtrl.showEdit($index)" /></td>
	</tr>
</table>

<div id="edit-form-div" ng-show="dataCtrl.edit_data">
<form id="edit-form" ng-submit="dataCtrl.saveEdit()">
	<table>
		<tr ng-repeat="(k, v) in dataCtrl.getFields('update')">
			<td>{{v['name']}}</td>
			<td><input type="text" name="k" id="k" ng-model="dataCtrl.edit_data[k]" /></td>
		</tr>
	</table>
</form>
</div>

</div>

