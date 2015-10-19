<%page args="baseclass,basetitle,query_filter=''" />


<div ng-controller="DataController as dataCtrl" baseclass="${baseclass}" basetitle="${basetitle}" queryfilter="${query_filter}">
	
	## <pre>
	## {{dataCtrl.baseclass}}
	## </pre>


	<input type="button" ng-click="dataCtrl.getList()" value="Refresh data" ng-hide="dataCtrl.data.length > 0" /><br />

	<table class="list">
		<tr>
			<th ng-repeat="(k, v) in dataCtrl.getFields('list')">{{v['name']}}</th>
			<th><img src="/static/img/icons/plus.png" ng-click="dataCtrl.showNew()" ng-show="dataCtrl.edit_active" /></th>
		</tr>
		<tr ng-repeat="obj in dataCtrl.data">
			<td ng-repeat="(k, v) in dataCtrl.getFields('list')">{{obj[k]}}</td>
			<td><img src="/static/img/icons/minus.png" alt="delete" title="delete" ng-click="dataCtrl.delete($index)" ng-show="dataCtrl.edit_active" /><img src="/static/img/icons/edit.png" alt="edit" title="edit" ng-click="dataCtrl.showEdit($index)" ng-show="dataCtrl.edit_active" /></td>
		</tr>
	</table>

	<div id="edit-form-div" title="Edit ${basetitle}">
	<form id="edit-form" ng-submit="dataCtrl.saveEdit()">
		<table>
			<tr ng-repeat="(k, v) in dataCtrl.form_fields">
				<td>{{v['name']}}</td>
				<td><input type="text" name="k" id="k" ng-model="dataCtrl.edit_data[k]" /></td>
			</tr>
		</table>
	</form>
	</div>

</div>