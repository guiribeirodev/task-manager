namespace OrganizeMyLife.Data;

public enum TodoState
{
    Draft,
    Todo,
    Doing,
    Done,
    Trash
}
public class Todo
{
    public int Id { get; init; }
    public required string Title { get; set; }
    public required string Description { get; set; }
    public TodoState State { get; set; }
    
    public int UserId { get; set; }
    // refactor null
    public virtual User User { get; set; } = null!;
    
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; set; }
}