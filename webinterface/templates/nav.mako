<%page args="active_tab" />

<ul class="tabrow">
	<li id="home"><a href="/">Home</a></li>
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