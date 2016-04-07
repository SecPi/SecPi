


var app = angular.module("SecPi", ['ngAnimate', 'ui.bootstrap']);

app.service('FlashService', ['$log', '$timeout',function($log, $timeout){
	var self = this;
	
	self.TYPE_INFO = 'info';
	self.TYPE_WARN = 'warn';
	self.TYPE_ERR = 'error';
	
	self.flash_messages = {};
	
	self.id = 0;
	
	self.flash = function(message,type,time){
		var id = ++self.id;
		if(!time){
			time = 5000;
		}
		msg = {message: message, type: type, id:id, showpin: false}
		self.flash_messages[id] = msg;
		
		msg.timeout = $timeout(self.removeFlash, time, true, id)	
	};
	
	self.cancelTimeout = function(id){
		if(self.flash_messages.hasOwnProperty(id)){
			$timeout.cancel(self.flash_messages[id].timeout)
		}
	}
	
	self.removeFlash = function(id){
		if(self.flash_messages.hasOwnProperty(id)){
			delete self.flash_messages[id];
		}
	};
	
	self.handle_error = function(response){
		self.flash(('Error with status ' +response.status +' while retrieving data!'), self.TYPE_ERR);
	}
}]);


app.service('HTTPService', ['$http', 'FlashService', function($http, FlashService){
	var self = this;
	
	self.post = function(path, data, success_func, err_func){
		$http.post(path, data).then(
			function (response) {
				// success
				if(response.data['status'] == 'success'){
					if(typeof success_func !== 'undefined'){
						success_func(response.data['data'], response.data['message']);
					}
				}
				else{
					FlashService.flash(response.data['message'], FlashService.TYPE_ERR, 5000);
					if(typeof err_func !== 'undefined'){
						err_func();
					}
				}
			},
			FlashService.handle_error
		);
	}
	
}]);

app.controller('FlashController', ['FlashService', '$timeout', function(FlashService, $timeout){
	var self = this;
	
	self.messages = FlashService.flash_messages;
	
	self.flash = function(message,type){
		FlashService.flash(message,type);
	}
	
	self.enter = function(id){
		self.messages[id].showpin=true;
		FlashService.cancelTimeout(id);
	}
	
	self.leave = function(id){
		self.messages[id].showpin=false;
		if(!self.messages[id].pinned){ // not pinned, start hide timeout
			self.messages[id].timeout = $timeout(function(){ FlashService.removeFlash(id); }, 1000);
		}
	}
	
	self.togglePin = function(id){
		if(self.messages[id].pinned){
			self.messages[id].pinned = false;
		}
		else{
			self.messages[id].pinned = true;
		}
	}
}])

function DataModalController($uibModalInstance, dataCtrl){
	var self = this;
	self.dataCtrl = dataCtrl;
}

app.controller('DataController', ['$uibModal', '$http', '$log', '$scope', '$timeout', '$attrs', 'FlashService', 'HTTPService', function($uibModal, $http, $log, $scope, $timeout, $attrs, FlashService, HTTPService){
	var self = this;
	
	if (!$attrs.baseclass) throw new Error("No class defined!");
	if (!$attrs.basetitle) throw new Error("No title defined!");
	
	self.baseclass = $attrs.baseclass;
	self.basetitle = $attrs.basetitle;
	
	if ($attrs.queryfilter){
		self.query_filter = $attrs.queryfilter;
	}
	if ($attrs.querysort){
		self.query_sort = $attrs.querysort;
	}
	
	self.dialogTitle = "Edit";
	
	self.data = [];
	self.fields = {};
	self.form_fields = {}
	
	self.edit_data = null;
	self.edit_id = -1;
	self.orig_data = null;
	
	self.loading = true;
	
	
	self.edit_active = true;
	HTTPService.post('/setups/list', {"filter":"active_state==1"},
		function(data, msg){
			// FlashService.flash("got data: "+ angular.toJson(data), FlashService.TYPE_INFO);
			if(data.length > 0){ // we got an active setup, disable edit
				self.edit_active = false;
			}
		}
	);
	
	
	self.fetchFields = function(){
		HTTPService.post('/' +self.baseclass+'/fieldList', {},
			function(data, msg){
				self.fields = data;
			}
		);
	}
	
	self.getFields = function(filter){
		return self.filter_fields(filter);
	}
	
	self.filter_fields = function(filter) {
		var filtered_fields = {};
		
		for (var key in self.fields) {
			if (self.fields.hasOwnProperty(key)) {
				if($.inArray(filter, self.fields[key]['visible']) >= 0){
					filtered_fields[key] = self.fields[key];
				}
			}
		}
		
		return filtered_fields;
	}
	
	
	self.getList = function(){
		self.loading = true;
		$log.log('fetching list')
		var list_data = {}
		if(self.query_filter){
			list_data["filter"] = self.query_filter
		}
		if(self.query_sort){
			list_data["sort"] = self.query_sort
		}
		
		HTTPService.post('/'+self.baseclass+'/list', list_data,
			function(data, msg){
				self.data = data;
				self.loading = false;
			},
			function(){
				self.loading = false;
			}
		);
	};
	
	self.showEdit = function(id){
		self.dialogTitle = "Edit";
		self.form_fields = self.getFields('update')
		self.edit_data = jQuery.extend(true, {}, self.data[id])
		self.edit_id = id;
		self.orig_data = self.data[id];
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/angular-edit.html',
			controller: ['$uibModalInstance', 'dataCtrl', DataModalController],
			controllerAs: 'dataModCtrl',
			size: 'sm',
			resolve: {
				dataCtrl: function(){ return self }
			}
		});
		self.dialog.result.then(function(){/* manual close */}, function(){ /* close by click on bg */ self.cancelEdit() })
	};
	
	self.saveEdit = function(){
		self.loading = true;
		$log.log("saving stuff")
		if(self.edit_id == -1){ // if edit id is -1 we are adding a new one
			HTTPService.post('/'+self.baseclass+'/add', self.edit_data,
				function(data, msg){
					FlashService.flash(msg, FlashService.TYPE_INFO)
					
					// self.data.push(self.edit_data); // won't get id of saved element
					self.getList();
					
					self.orig_data = null;
					self.edit_data = null;
					self.edit_id = -1;
					
					self.dialog.close(msg)
					self.loading = false;
				},
				function(){
					self.loading = false;
				}
			);
		}
		else{
			HTTPService.post('/'+self.baseclass+'/update', self.edit_data,
				function(data, msg){
					FlashService.flash(msg, FlashService.TYPE_INFO)
					self.data[self.edit_id] = self.edit_data;
					self.orig_data = null;
					self.edit_data = null;
					self.edit_id = -1;
					self.dialog.close(msg)
					self.loading = false;
				},
				function(){
					self.loading = false;
				}
			);
		}
	};
	
	self.cancelEdit = function(){
		$log.log("cancel "+self.edit_id);
		self.orig_data = null;
		self.edit_data = null;
		self.edit_id = -1;
		self.dialog.close("Canceled edit!");
	};
	
	self.showNew = function(){
		self.dialogTitle = "New";
		self.form_fields = self.getFields('add')
		self.edit_data = {};
		self.edit_id = -1;
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/angular-edit.html',
			controller: ['$uibModalInstance', 'dataCtrl', DataModalController],
			controllerAs: 'dataModCtrl',
			size: 'sm',
			resolve: {
				dataCtrl: function(){ return self }
			}
		});
		self.dialog.result.then(function(){/* manual close */}, function(){ /* close by click on bg */ self.cancelEdit() })
	};
	
	self.showDelete = function(delId){
		self.delID = self.data[delId]["id"];
		self.delNo = delId;
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/confirm-delete.html',
			controller: ['$uibModalInstance', 'dataCtrl', DataModalController],
			controllerAs: 'dataModCtrl',
			size: 'sm',
			resolve: {
				dataCtrl: function(){ return self }
			}
		});
	};
	
	self.delete = function(){
		HTTPService.post('/'+self.baseclass+'/delete', {id: self.delID},
			function(data, msg){
				FlashService.flash(msg, FlashService.TYPE_INFO)
				self.data.splice(self.delNo, 1);
				self.dialog.close("Canceled delete!")
				self.loading = false;
			},
			function(){
				self.loading = false;
			}
		);
	}
	
	self.cancelDelete = function(){
		self.delID = -1;
		self.delNo = -1;
		self.dialog.close("Canceled delete!")
	}
	
	
	self.copy = function(copyId){
		self.loading = true;
		self.dialogTitle = "Copy";
		self.form_fields = self.getFields('add')
		self.edit_data = jQuery.extend(true, {}, self.data[copyId])
		self.edit_id = -1;
		self.orig_data = self.data[copyId];
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/angular-edit.html',
			controller: ['$uibModalInstance', 'dataCtrl', DataModalController],
			controllerAs: 'dataModCtrl',
			size: 'sm',
			resolve: {
				dataCtrl: function(){ return self }
			}
		});
		self.dialog.result.then(function(){/* manual close */}, function(){ /* close by click on bg */ self.cancelEdit() })
		self.loading = false;
	}
	
	self.export = function(exportId){
		expdata = [
			{
				type: self.baseclass,
				data: self.data[exportId]
			}
		]
		self.export_data = angular.toJson(expdata, true);
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/export.html',
			controller: ['$uibModalInstance', 'dataCtrl', DataModalController],
			controllerAs: 'dataModCtrl',
			size: 'lg',
			resolve: {
				dataCtrl: function(){ return self }
			}
		});
		self.dialog.result.then(function(){/* manual close */}, function(){ /* close by click on bg */ self.cancelExport() })
	}
	
	self.exportTable = function(){
		expdata = []
		for(var i=0;i<self.data.length;i++){
			expdata.push({
				type: self.baseclass,
				data: self.data[i]
			})
		}
		
			
		
		self.export_data = angular.toJson(expdata, true);
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/export.html',
			controller: ['$uibModalInstance', 'dataCtrl', DataModalController],
			controllerAs: 'dataModCtrl',
			size: 'lg',
			resolve: {
				dataCtrl: function(){ return self }
			}
		});
		self.dialog.result.then(function(){/* manual close */}, function(){ /* close by click on bg */ self.cancelExport() })
	}
	
	self.cancelExport = function(){
		self.export_data = null;
		self.dialog.close("closing");
	}
	
	self.showImport = function(){
		self.import_text = null;
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/import.html',
			controller: ['$uibModalInstance', 'dataCtrl', DataModalController],
			controllerAs: 'dataModCtrl',
			size: 'lg',
			resolve: {
				dataCtrl: function(){ return self }
			}
		});
		self.dialog.result.then(function(){/* manual close */}, function(){ /* close by click on bg */ self.cancelImport() })
	}
	
	self.import = function(){
		self.loading = true;
		self.import_data = angular.fromJson(self.import_text)
		if(self.import_data){
			for(var i=0;i<self.import_data.length;i++){
				if(self.import_data[i]["type"]!=null && self.import_data[i]["data"]!=null){
					HTTPService.post('/'+self.import_data[i]["type"]+'/add', self.import_data[i]["data"],
						function(data, msg){
							FlashService.flash(msg, FlashService.TYPE_INFO)
							self.finishImport();
						},
						function(){
						}
					);
				}
			}
		}
		self.dialog.close("imported")
		self.loading = false;
	}
	
	self.import_counter = 0;
	
	self.finishImport = function(){
		self.import_counter++;
		$log.log(self.import_counter)
		$log.log(self.import_data.length)
		if(self.import_counter==self.import_data.length){
			self.getList();
			self.import_counter=0;
		}
	}
	
	self.cancelImport = function(){
		self.import_data = null;
		self.dialog.close("closing");
	}
	
	self.fetchFields();
	self.getList();
	
	self.loading = false;
}]);


app.controller('AckController', ['$http', '$log', '$interval', '$attrs', 'FlashService', 'HTTPService', function($http, $log, $interval, $attrs, FlashService, HTTPService){
	var self = this;
	
	if (!$attrs.ackclass) throw new Error("No class defined!");
	
	if ($attrs.sort){
		self.sort = $attrs.sort;
	}
	
	self.ackclass = $attrs.ackclass;
	
	self.btnText = "stop refresh"
	
	
	self.entries = [];
	
	self.fetchData = function(){
		HTTPService.post('/' +self.ackclass +'s/list', {"filter":"ack==0", "sort": self.sort},
			function(data, msg){
				if(angular.toJson(data) != angular.toJson(self.entries)){
					self.entries = data;
				}
			}
		);
	};
	
	self.ack = function(ent_id){
		HTTPService.post('/' +self.ackclass +'s/ack', {"id":self.entries[ent_id].id},
			function(data, msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
				self.entries.splice(ent_id, 1);
			}
		);
	}
	
	self.ackAll = function(){
		HTTPService.post('/' +self.ackclass +'s/ackAll', {},
			function(data, msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
				self.fetchData();
			}
		);
	}
	
	self.refresh = function(){
		self.fetchData();
	}
	
	self.toggleRefresh = function(){
		if(self.refresh_inter){
			self.stopRefresh();
		}
		else{
			self.startRefresh();
		}
	}
	
	self.startRefresh = function(){
		// refresh list every 5 seconds
		if(!self.refresh_inter){
			self.refresh_inter = $interval(self.refresh, 5000);
			FlashService.flash('Started refresh of messages!', FlashService.TYPE_INFO, 2000);
			//$('#refresh_toggle_'+self.ackclass).prop('value', "stop refresh");
			self.btnText = "stop refresh";
		}
	}
	
	self.stopRefresh = function(){
		if(self.refresh_inter){
			$interval.cancel(self.refresh_inter);
			self.refresh_inter = null;
			FlashService.flash('Stopped refresh of messages!', FlashService.TYPE_INFO, 2000);
			//$('#refresh_toggle_'+self.ackclass).prop('value', "start refresh");
			self.btnText = "start refresh";
		}
	}
	
	self.fetchData();
	
	self.startRefresh()
}]);



app.controller('ActivateController', ['$http', '$log', '$interval', 'FlashService', 'HTTPService', function($http, $log, $interval, FlashService, HTTPService){
	var self = this;
	
	self.inactive_setups = [];
	self.active_setups = [];
	
	self.fetch_active = function(){
		HTTPService.post('/setups/list', {"filter":"active_state==1"}, function(data, msg){self.active_setups = data})
	}
	
	self.fetch_inactive = function(){
		HTTPService.post('/setups/list', {"filter":"active_state==0"}, function(data, msg){self.inactive_setups = data})
	}
	
	self.activate = function(){
		if(self.activate_setup){
			HTTPService.post('/activate', {"id": self.activate_setup.id}, 
				function(data,msg){
					FlashService.flash(msg, FlashService.TYPE_INFO);
					self.fetch_active();
					self.fetch_inactive();
				}
			);
		}
	}
	
	self.deactivate = function(){
		if(self.deactivate_setup){
			HTTPService.post('/deactivate', {"id": self.deactivate_setup.id}, 
				function(data,msg){
					FlashService.flash(msg, FlashService.TYPE_INFO);
					self.fetch_active();
					self.fetch_inactive();
				}
			);
		}	
	}
	
	self.fetch_active();
	self.fetch_inactive();
}]);


app.controller('ConfigController', ['$log', 'FlashService', 'HTTPService', function($log, FlashService, HTTPService){
	var self = this;
	
	
}]);


function RelationshipModalController($uibModalInstance, rlCtrl){
	var self = this;
	self.rlCtrl = rlCtrl;
}

app.controller('RelationshipController', ['$log', '$timeout', '$attrs', '$uibModal', 'FlashService', 'HTTPService', function($log, $timeout, $attrs, $uibModal, FlashService, HTTPService){
	var self = this;
	
	if (!$attrs.leftclass) throw new Error("No left class defined!");
	if (!$attrs.rightclass) throw new Error("No right class defined!");
	
	self.leftclass = $attrs.leftclass;
	self.rightclass = $attrs.rightclass;
	
	self.leftname = $attrs.leftname?$attrs.leftname:$attrs.leftclass;
	self.rightname = $attrs.rightname?$attrs.rightname:$attrs.rightclass;
	
	
	self.lefts_rights = [];
	self.lefts = [];
	self.rights = [];
	self.left_del = -1;
	self.right_del = -1;
	
	
	self.edit_active = true;
	HTTPService.post('/setups/list', {"filter":"active_state==1"},
		function(data, msg){
			// FlashService.flash("got data: "+ angular.toJson(data), FlashService.TYPE_INFO);
			if(data.length > 0){ // we got an active setup, disable edit
				self.edit_active = false;
			}
		}
	);
	
	self.fetchData = function(){
		HTTPService.post('/' +self.leftclass +'s' +self.rightclass +'s/list', {},
			function(data,msg){
				self.lefts_rights = data;		
			}
		);
		
		HTTPService.post('/' +self.leftclass +'s/list', {},
			function(data,msg){
				self.lefts = data;
			}
		);
		
		HTTPService.post('/' +self.rightclass +'s/list', {},
			function(data,msg){
				self.rights = data;
			}
		);
	}
	
	self.showAdd = function(){
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/rel-edit.html',
			controller: ['$uibModalInstance', 'rlCtrl', RelationshipModalController],
			controllerAs: 'rlModCtrl',
			size: 'sm',
			resolve: {
				rlCtrl: function(){ return self }
			}
		});
	}
	
	self.save = function(){
		var dat = {};
		dat[self.leftclass+"_id"] = self.left.id;
		dat[self.rightclass+"_id"] = self.right.id;
		HTTPService.post('/' +self.leftclass +'s' +self.rightclass +'s/add', dat,
			function(data, msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
				self.fetchData();
				self.dialog.close(msg);
			}
		);
		
		
	}
	
	self.cancel = function(){
		self.dialog.close("canceled");
	}
	
	self.showDelete = function(left_id, right_id){
		self.left_del = left_id;
		self.right_del = right_id;
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/confirm-rel-delete.html',
			controller: ['$uibModalInstance', 'rlCtrl', RelationshipModalController],
			controllerAs: 'rlModCtrl',
			size: 'sm',
			resolve: {
				rlCtrl: function(){ return self }
			}
		});
	}
	
	self.delete = function(){
		var dat = {};
		dat[self.leftclass+"_id"] = self.left_del;
		dat[self.rightclass+"_id"] = self.right_del;
		HTTPService.post('/' +self.leftclass +'s' +self.rightclass +'s/delete', dat,
			function(data, msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
				self.fetchData();
				self.dialog.close(msg);
			}
		);
	}
	
	self.fetchData();
}]);


app.controller('TestController', ['$http', '$log', '$interval', 'FlashService', 'HTTPService', function($http, $log, $interval, FlashService, HTTPService){
	var self = this;
	
	self.ftypes = ["info", "warn", "error"]
	self.msgtime = 5000;
	self.msgtext = "Test message!"
	
	self.push_flash = function(){
		var rand = Math.floor(Math.random() * 10)%self.ftypes.length;
		FlashService.flash("Flash message getting very very very long! What should we do now ohnoeeees asdfasdfasdfasdfasdf!!!! "+new Date(), self.ftypes[rand])
	}
	
	self.showFlash = function(){
		FlashService.flash(self.msgtext, FlashService.TYPE_INFO, self.msgtime);
	}
	
	/*HTTPService.post('/test', {},
		function(data,msg){
			FlashService.flash(msg, FlashService.TYPE_INFO);
		})
	*/
	//self.flash_inter = $interval(self.push_flash, 2000);
}]);


app.controller('CredentialsController', ['$log', 'FlashService', 'HTTPService', function($log, FlashService, HTTPService){
	var self = this;

	self.username = "admin";
	self.password = "";
		
	self.changeCredentials = function(){
		HTTPService.post('/change_login', {"username": self.username, "password": self.password},
			function(data,msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
			}
		);
		
	}
	
}]);


function AlarmDataModalController($uibModalInstance, dataCtrl){
	var self = this;
	self.dataCtrl = dataCtrl;
}

app.controller('AlarmDataController', ['$log', '$timeout', '$uibModal', 'FlashService', 'HTTPService', function($log, $timeout, $uibModal, FlashService, HTTPService){
	var self = this;
	
	self.folders = [];
	self.cur_folder = null;
	self.files = null;
	self.img = null;
	
	self.showFolder = function(id){
		self.cur_folder = self.folders[id]
		self.fetchFiles(self.cur_folder.name)
		self.dialog = $uibModal.open({
			templateUrl: '/static/html/alarmdata-dialog.html',
			controller: ['$uibModalInstance', 'dataCtrl', AlarmDataModalController],
			controllerAs: 'dataModCtrl',
			size: 'lg',
			resolve: {
				dataCtrl: function(){ return self }
			}
		});
		self.dialog.result.then(function(){/* manual close */}, function(){ /* close by click on bg */ self.hideFolder() })
	}
	
	self.hideFolder = function(){
		self.cur_folder = null;
		self.dialog.close("close");
	}
	
	
	self.fetchFolders = function(){
		HTTPService.post('/alarmdata/list', {},
			function(data,msg){
				self.folders = data;
			}
		);
	}
	
	self.fetchFiles = function(folder){
		HTTPService.post('/alarmdata/listFiles', {'folder':folder},
			function(data,msg){
				self.files = data;
			}
		);
	}
	
	
	self.extractFile = function(folder, name){
		HTTPService.post('/alarmdata/extract', {'dir':folder, 'name':name},
			function(data,msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
				self.fetchFiles(folder);
			}
		);
	}
	
	self.showImg = function(folder, name, type){
		self.img = "/alarmdata/show_img?name=" +folder+"/"+name +"&mimetype=image/"+type
	}
	
	
	self.fetchFolders();
	
}]);

app.controller('NavController', ['$uibModal', '$log', '$scope', '$interval', 'FlashService', 'HTTPService', function($uibModal, $log, $scope, $interval, FlashService, HTTPService){
	var self = this;
	
	self.showing = true;
	self.unread_count = 0;
	
	self.toggle = function(){
		self.showing = !self.showing;
	}
	
	self.fetchCount = function(){
		self.unread_count = 0;
		HTTPService.post('/alarms/list', {"filter":"ack==0"},
			function(data, msg){
				self.unread_count += data.length;
			}
		);
		HTTPService.post('/logs/list', {"filter":"ack==0"},
			function(data, msg){
				self.unread_count += data.length;
			}
		);
	}
	
	self.toggleRefresh = function(){
		if(self.refresh_inter){
			self.stopRefresh();
		}
		else{
			self.startRefresh();
		}
	}
	
	self.startRefresh = function(){
		// refresh count every 20 seconds
		if(!self.refresh_inter){
			self.refresh_inter = $interval(self.fetchCount, 30000);
		}
	}
	
	self.stopRefresh = function(){
		if(self.refresh_inter){
			$interval.cancel(self.refresh_inter);
			self.refresh_inter = null;
		}
	}
	
	
	self.fetchCount();
	
	self.startRefresh();
	
}]);

// http://stackoverflow.com/questions/28050980/how-can-i-modify-an-angularjs-bootstrap-dropdown-select-so-that-it-does-not-us
app.directive('dropdown', function() {
	return {
	  restrict: 'E',
	  require: '^ngModel',
	  scope: {
		ngModel: '=', // selection
		items: '=',   // items to select from
		callback: '&' // callback
	  },
	  link: function(scope, element, attrs) {
		element.on('click', function(event) {
		  event.preventDefault();
		});
		
		scope.default = 'Please select item';
  
		// selection changed handler
		scope.select = function(item) {
		  scope.ngModel = item;
		  if (scope.callback) {
			scope.callback({ item: item });
		  }
		};
	  },
	  templateUrl: '/static/html/dropdown-template.html'
	};
  })
