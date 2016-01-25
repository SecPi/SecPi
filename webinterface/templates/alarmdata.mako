<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "alarmdata" %></%def>

<div ng-controller="AlarmDataController as dataCtrl">
	<input type="button" value="fetch" ng-click="dataCtrl.fetchFolders()" />
	<table id="alarmdata">
		<tr>
			<th>Name</th>
			<th>Time</th>
			<th>Size</th>
		</tr>
		<tr ng-repeat="f in dataCtrl.folders">
			<td class="data_click" ng-click="dataCtrl.showFolder($index)">{{f.name}}</td>
			<td>{{f.mtime}}</td>
			<td>{{f.hsize}}</td>
		</tr>
	</table>
	<div id="folder_content" ng-show="dataCtrl.cur_folder">
		<p ng-repeat="fi in dataCtrl.cur_folder.files">
			<a href="/alarmdata/download?name={{dataCtrl.cur_folder.name}}/{{fi}}">{{fi}}</a>
		</p>
	</div>
</div>


