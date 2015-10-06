<%page args="active_tab" />

<ul class="tabrow">
	<li id="home"><a href="/">Home</a></li>
	<li id="activate"><a href="/activate">Activate</a></li>
	<li id="setups"><a href="/setups">Setups</a></li>
	<li id="alarms"><a href="/alarms">Alarms</a></li>
	<li id="workers"><a href="/workers">Workers</a></li>
	<li id="actions"><a href="/actions">Actions</a></li>
	<li id="notifiers"><a href="/notifiers">Notifiers</a></li>
</ul>



<script type="text/javascript">
	$("#${active_tab}").addClass('selected')
</script>