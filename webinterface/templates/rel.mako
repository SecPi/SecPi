<%page args="leftclass,leftname,rightclass,rightname" />

<div ng-controller="RelationshipController as rlCtrl" leftclass="${leftclass}" leftname="${leftname}" rightclass="${rightclass}" rightname="${rightname}">
	<table class="list">
		<tr>
			<th>${leftname}</th>
			<th>${rightname}</th>
			<th><img src="/static/img/icons/plus.png" ng-click="rlCtrl.showAdd()" class="pointer" ng-show="rlCtrl.edit_active" /><img src="/static/img/icons/refresh.png" ng-click="rlCtrl.fetchData()" class="pointer" /></th>
		</tr>
		<tr ng-repeat="obj in rlCtrl.lefts_rights">
			<td>{{obj['name']}}</td>
			<td><p ng-repeat="z in obj['${rightclass}s']">{{z.name}} <img src="/static/img/icons/minus.png" alt="delete" title="delete" ng-click="rlCtrl.delete(obj.id, z.id)" class="pointer" ng-show="rlCtrl.edit_active" /></p></td>
			<td></td>
		</tr>
	</table>
	
	<div id="sz-form" title="Add">
		${leftname}: <select name="${leftclass}" id="${leftclass}"
			ng-options="l.name for l in rlCtrl.lefts track by l.id"
			ng-model="rlCtrl.left"></select><br />
		${rightname}: <select name="${rightclass}" id="${rightclass}"
			ng-options="r.name for r in rlCtrl.rights track by r.id"
			ng-model="rlCtrl.right"></select>
	</div>
</div>