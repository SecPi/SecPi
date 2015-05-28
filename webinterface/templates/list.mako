<%inherit file="main.mako"/>

% if data is not None and len(data) > 0 and fields is not None and len(fields)>0:
	<table class="list">
		<tr class="listheader">
		% for field,desc in fields.iteritems():
			<th>${desc}</th>
		%endfor
			<th>&nbsp;</th><!-- for delete button -->
		</tr>
		% for obj in data:
			<tr>
			% for field, desc in fields.iteritems():
				<td>${obj.__dict__[field]}</td>
			% endfor
				<td><a href="delete?id=${obj.id}">delete</a></td>
			</tr>
		% endfor
	</table>
% else:
	No data found!
% endif