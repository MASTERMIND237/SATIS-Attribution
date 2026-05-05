from .student import Student, StudentCreate, StudentRead
from .widget import Widget, WidgetCreate, WidgetRead, WidgetProperty, WidgetPropertyCreate, WidgetPropertyRead
from .assignment import Assignment, AssignmentRead
from .feedback import UsefulnessFeedback

Student.update_forward_refs()
Widget.update_forward_refs()
Assignment.update_forward_refs()
