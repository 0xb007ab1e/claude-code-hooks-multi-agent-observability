using Microsoft.AspNetCore.Mvc.Testing;
using System.Net.Http.Json;
using System.Text.Json;
using Xunit;

namespace AspNetCoreSkeleton.Tests;

public class ApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly HttpClient _client;

    public ApiTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task Get_Root_ReturnsSuccessAndCorrectMessage()
    {
        // Act
        var response = await _client.GetAsync("/");

        // Assert
        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        var json = JsonDocument.Parse(content);
        Assert.Equal("ASP.NET Core skeleton API is running!", json.RootElement.GetProperty("message").GetString());
    }

    [Fact]
    public async Task Get_Health_ReturnsHealthyStatus()
    {
        // Act
        var response = await _client.GetAsync("/health");

        // Assert
        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        var json = JsonDocument.Parse(content);
        Assert.Equal("healthy", json.RootElement.GetProperty("status").GetString());
        Assert.True(json.RootElement.TryGetProperty("timestamp", out _));
    }

    [Fact]
    public async Task Get_Users_ReturnsEmptyList()
    {
        // Act
        var response = await _client.GetAsync("/api/users");

        // Assert
        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        var json = JsonDocument.Parse(content);
        Assert.Equal(0, json.RootElement.GetProperty("users").GetArrayLength());
    }

    [Fact]
    public async Task Post_User_CreatesUser()
    {
        // Arrange
        var userData = new
        {
            name = "John Doe",
            email = "john@example.com"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/users", userData);

        // Assert
        response.EnsureSuccessStatusCode();
        var content = await response.Content.ReadAsStringAsync();
        var json = JsonDocument.Parse(content);
        Assert.Equal("John Doe", json.RootElement.GetProperty("name").GetString());
        Assert.Equal("john@example.com", json.RootElement.GetProperty("email").GetString());
        Assert.True(json.RootElement.TryGetProperty("id", out _));
    }

    [Fact]
    public async Task Get_NonexistentUser_ReturnsNotFound()
    {
        // Act
        var response = await _client.GetAsync("/api/users/999");

        // Assert
        Assert.Equal(System.Net.HttpStatusCode.NotFound, response.StatusCode);
    }
}
