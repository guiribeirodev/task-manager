using OrganizeMyLife.Data;

public class TodoItemDto
{
    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public TodoState State { get; set; }
    public int UserId { get; set; }

    public TodoItemDto() { }
    public TodoItemDto(OrganizeMyLife.Data.Todo todoItem)
    {
        Id = todoItem.Id;
        Title = todoItem.Title;
        Description = todoItem.Description;
        State = todoItem.State;
        UserId = todoItem.UserId;
    }
}