<%page args="baseclass,basetitle,query_filter=''" />


<div ng-controller="DataController as dataCtrl" baseclass="${baseclass}" basetitle="${basetitle}" queryfilter="${query_filter}">
	
	## <pre>
	## {{dataCtrl.baseclass}}
	## </pre>

	<div class="loading" ng-show="dataCtrl.loading"></div>

	<table class="table table-striped">
		<thead>
			<tr>
				<th ng-repeat="(k, v) in dataCtrl.getFields('list')">{{v['name']}}</th>
				<th class="edit_col">
					<img src="/static/img/icons/plus.png" ng-click="dataCtrl.showNew()" ng-show="dataCtrl.edit_active" class="pointer" />
					<img src="/static/img/icons/refresh.png" ng-click="dataCtrl.getList()" class="pointer" />
					<img src="/static/img/icons/table-export.png" alt="export all" title="export all" ng-click="dataCtrl.exportTable()" class="pointer" />
				</th>
			</tr>
		</thead>
		<tbody>
			<tr ng-repeat="obj in dataCtrl.data">
				<td ng-repeat="(k, v) in dataCtrl.getFields('list')">{{obj[k]}}</td>
				<td class="edit_col">
					<img src="/static/img/icons/minus.png" alt="delete" title="delete" ng-click="dataCtrl.showDelete($index)" ng-show="dataCtrl.edit_active" class="pointer" />
					<img src="/static/img/icons/edit.png" alt="edit" title="edit" ng-click="dataCtrl.showEdit($index)" ng-show="dataCtrl.edit_active" class="pointer" />
					<img src="/static/img/icons/copy.png" alt="copy" title="copy" ng-click="dataCtrl.copy($index)" ng-show="dataCtrl.edit_active" class="pointer" />
					<img src="/static/img/icons/export.png" alt="export" title="export" ng-click="dataCtrl.export($index)" class="pointer" />
				</td>
			</tr>
		</tbody>
	</table>
</div>
