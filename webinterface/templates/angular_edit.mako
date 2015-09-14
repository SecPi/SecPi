<%page args="baseclass,basetitle" />


<div ng-controller="DataController as dataCtrl" baseclass="${baseclass}" basetitle="${basetitle}">

	<div id="flash_message" ng-repeat="msg in dataCtrl.flash_messages" ng-class="msg.type" ng-show="msg.message != null">
		{{msg.message}}
	</div>

	## <pre>
	## {{dataCtrl.baseclass}}
	## </pre>


	<input type="button" ng-click="dataCtrl.getList()" value="Refresh data" ng-hide="dataCtrl.data.length > 0" /><br />

	<table class="list" ng-show="dataCtrl.data.length > 0">
		<tr>
			<th ng-repeat="(k, v) in dataCtrl.getFields('list')">{{v['name']}}</th>
			<th><img src="/static/img/icons/plus.png" ng-click="dataCtrl.showNew()" /></th>
		</tr>
		<tr ng-repeat="obj in dataCtrl.data">
			<td ng-repeat="(k, v) in dataCtrl.getFields('list')">{{obj[k]}}</td>
			<td><img src="/static/img/icons/minus.png" alt="delete" title="delete" ng-click="dataCtrl.delete($index)" /><img src="/static/img/icons/edit.png" alt="edit" title="edit" ng-click="dataCtrl.showEdit($index)" /></td>
		</tr>
	</table>

	<div id="edit-form-div" ng-show="dataCtrl.edit_data" title="Edit ${basetitle}">
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