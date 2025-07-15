using Microsoft.AspNetCore.Mvc;

namespace AspNetCoreSkeleton.Controllers;

[ApiController]
[Route("")]
public class ApiController : ControllerBase
{
    [HttpGet("")]
    public IActionResult Root()
    {
        return Ok(new { message = "ASP.NET Core skeleton API is running!" });
    }

    [HttpGet("health")]
    public IActionResult Health()
    {
        return Ok(new
        {
            status = "healthy",
            timestamp = DateTime.UtcNow.ToString("O")
        });
    }
}
