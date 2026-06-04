namespace OrganizeMyLife.Data;

public class User
{
    public int Id { get; init; }
    public required string Username { get; set; }
    public required string Password { get; set; }
    public required string Email { get; set; }
    
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; init; }
    
    public virtual ICollection<Todo> Todos { get; set; } = new HashSet<Todo>();
}