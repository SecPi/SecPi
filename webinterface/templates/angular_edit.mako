<%page args="baseclass,basetitle,query_filter=''" />


<div ng-controller="DataController as dataCtrl" baseclass="${baseclass}" basetitle="${basetitle}" queryfilter="${query_filter}">
	
	## <pre>
	## {{dataCtrl.baseclass}}
	## </pre>

	<div class="loading" ng-show="dataCtrl.loading"></div>

	<table class="table table-striped">
		<thead>
			<tr class="pointer" uib-popover-template="'/static/html/table-popover.html'" popover-trigger="outsideClick" popover-placement="top">
				<th ng-repeat="(k, v) in dataCtrl.getFields('list')">{{v['name']}}</th>
			</tr>
		</thead>
		<tbody>
			<tr ng-repeat="obj in dataCtrl.data" class="pointer" uib-popover-template="'/static/html/edit-popover.html'" popover-trigger="outsideClick" popover-placement="top">
				<td ng-repeat="(k, v) in dataCtrl.getFields('list')">{{obj[k]}}</td>
			</tr>
		</tbody>
	</table>
</div>
