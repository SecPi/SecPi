<%page args="active_tab" />

<div id="navbutton" ng-click="navCtrl.toggle()">
	<span class="icon-bar"></span>
	<span class="icon-bar"></span>
	<span class="icon-bar"></span> 
</div>

<ul class="tabrow" ng-class="navCtrl.showing?'nav-state1':'nav-state2'">
	<li id="home"><a href="/">Home <span class="badge" ng-show="navCtrl.unread_count>0">{{navCtrl.unread_count}}</span></a></li>
	<li id="data"><a href="/alarmdata">Alarm Data</a></li>
	<li id="setups"><a href="/setups">Setups</a></li>
	<li id="alarms"><a href="/alarms">Alarms</a></li>
	<li id="workers"><a href="/workers">Workers</a></li>
	<li id="actions"><a href="/actions">Actions</a></li>
	<li id="notifiers"><a href="/notifiers">Notifiers</a></li>
	<li id="change_credentials"><a href="/change_credentials">Change Login</a></li>
</ul>


<script type="text/javascript">
	$("#${active_tab}").addClass('selected')
</script>