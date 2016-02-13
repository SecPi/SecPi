<%page args="leftclass,leftname,rightclass,rightname" />

<div ng-controller="RelationshipController as rlCtrl" leftclass="${leftclass}" leftname="${leftname}" rightclass="${rightclass}" rightname="${rightname}">
	<table class="table table-striped">
		<thead>
			<tr>
				<th>${leftname}</th>
				<th>${rightname}</th>
				<th><img src="/static/img/icons/plus.png" ng-click="rlCtrl.showAdd()" class="pointer" ng-show="rlCtrl.edit_active" /><img src="/static/img/icons/refresh.png" ng-click="rlCtrl.fetchData()" class="pointer" /></th>
			</tr>
		</thead>
		<tbody>
			<tr ng-repeat="obj in rlCtrl.lefts_rights">
				<td>{{obj['name']}}</td>
				<td colspan="2"><span ng-repeat="z in obj['${rightclass}s']">{{z.name}} <img src="/static/img/icons/minus.png" alt="delete" title="delete" ng-click="rlCtrl.showDelete(obj.id, z.id)" class="pointer" ng-show="rlCtrl.edit_active" /><br /></span></td>
			</tr>
		</tbody>
	</table>
</div>