<%inherit file="main.mako"/>

% if data is not None and len(data) > 0:
	<table>
		<tr>
		% for prop, val in vars(data[0]).iteritems():
			<th>${prop}</th>
		%endfor
		</tr>
		% for obj in data:
			<tr>
			% for prop, val in vars(obj).iteritems():
				<td>${val}</td>
			% endfor
				<td><a href="delete?id=${obj.id}">delete</a></td>
			</tr>
		% endfor
	</table>
% else:
	No data found!
% endif