<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "alarmdata" %></%def>

<div ng-controller="AlarmDataController as dataCtrl">
	<input type="button" value="fetch" ng-click="dataCtrl.fetchFolders()" />
	<table id="alarmdata">
		<tr>
			<th>Name</th>
			<th>Time</th>
		</tr>
		<tr ng-repeat="f in dataCtrl.folders">
			<td class="data_click" ng-click="dataCtrl.showFolder($index)">{{f.name}}</td>
			<td>{{f.mtime}}</td>
		</tr>
	</table>
	<div id="folder_content" ng-show="dataCtrl.cur_folder">
		<p ng-repeat="fi in dataCtrl.files">
			<a href="/alarmdata/download?name={{dataCtrl.cur_folder.name}}/{{fi}}">{{fi}}</a>
			
			<span ng-switch on="fi.slice(fi.lastIndexOf('.')+1)">
				<span ng-switch-when="zip">
					<img src="/static/img/icons/zipfile.png" class="pointer" ng-click="dataCtrl.extractFile(dataCtrl.cur_folder.name, fi)" title="Extract ZIP File" alt="Extract ZIP File" />
				</span>
				<span ng-switch-when="jpg">
					<img src="/static/img/icons/image.png" class="pointer" ng-click="dataCtrl.showImg(dataCtrl.cur_folder.name, fi, 'jpg')" title="Show Image" alt="Show Image" />
				</span>
				<span ng-switch-when="png">
					<img src="/static/img/icons/image.png" class="pointer" ng-click="dataCtrl.showImg(dataCtrl.cur_folder.name, fi, 'png')" title="Show Image" alt="Show Image" />
				</span>
				<span ng-switch-when="gif">
					<img src="/static/img/icons/image.png" class="pointer" ng-click="dataCtrl.showImg(dataCtrl.cur_folder.name, fi, 'gif')" title="Show Image" alt="Show Image" />
				</span>
			</span>
		</p>
	</div>
	<div ng-show="dataCtrl.img" id="img_container">
		<img id="file_img" ng-src="{{dataCtrl.img}}" ng-click="dataCtrl.img=null" class="pointer" />
	</div>
</div>


