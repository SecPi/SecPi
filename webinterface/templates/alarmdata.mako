<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "data" %></%def>

<div ng-controller="AlarmDataController as dataCtrl">
	<input type="button" value="fetch" class="btn btn-success" ng-click="dataCtrl.fetchFolders()" />
	<table id="alarmdata" class="table table-striped">
		<thead>
			<tr>
				<th>Name</th>
				<th>Time</th>
			</tr>
		</thead>
		<tbody>
			<tr ng-repeat="f in dataCtrl.folders">
				<td class="data_click" ng-click="dataCtrl.showFolder($index)">{{f.name}}</td>
				<td>{{f.mtime}}</td>
			</tr>
		</tbody>
	</table>
	<div ng-show="dataCtrl.img" id="img_container">
		<img id="file_img" ng-src="{{dataCtrl.img}}" ng-click="dataCtrl.img=null" class="pointer" />
	</div>
</div>


